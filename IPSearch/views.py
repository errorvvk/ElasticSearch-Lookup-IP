from django.shortcuts import render
from django.http import HttpResponse, response
from .form import IPForm
import requests
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta

elasticsearch = Elasticsearch([{'host':'localhost','port':9200}])
INDEX_NAME = "mytask"
DOC_TYPE = "ipdetails"

def home(request):
    context = {}
    form = IPForm(request.POST or None) 
    context['form']= form 
    if request.POST: 
        if form.is_valid(): 
            ip_address = form.cleaned_data.get("ip_address")

            ip_present = check_ip_address(ip_address)

            if ip_present:
                response_json = ip_present['_source']
            else:
                URL = f"https://api.threatminer.org/v2/host.php?q={ip_address}&rt=1"
                ip_response = requests.get(URL)
                response_json = ip_response.json()
                response_json["last-inserted"] = int(datetime.now().timestamp())

                insert_in_elasticsearch(ip_address, response_json)
            
            if response_json["status_code"] == '200':
                context["ip_status"] = response_json['status_message']
                context["ip_data"] = response_json["results"][0]
                context["ip"] = ip_address
            else:
                context["ip_status"] = response_json['status_message']

    
    return render(request, "home.html", context)

def insert_in_elasticsearch(ip_address, data):
    try:
        elasticsearch.index(index=INDEX_NAME,doc_type=DOC_TYPE,id=ip_address,body=data)

    except Exception as e:
        print(e)


def check_ip_address(ip_address):
    print(ip_address)
    try:
        # response = elasticsearch.get(index=INDEX_NAME,doc_type=DOC_TYPE,id=ip_address)
        last_48_hours = int((datetime.now() - timedelta(hours=48)).timestamp())
        query_body = {
            "query": {
                "bool": {
                "must": [
                    {
                    "match": {
                        "_id": ip_address
                    }
                    }
                ],
                "filter": [
                    {
                    "range": {
                        "last-inserted": {
                        "gte": last_48_hours
                        }
                    }
                    }
                ]
                }
            }
            }

        response = elasticsearch.search(index=INDEX_NAME, doc_type=DOC_TYPE, body=query_body)

        if response["hits"]["hits"]:
            response = response["hits"]["hits"][0]

            return response

        return False
    except:
        return False
