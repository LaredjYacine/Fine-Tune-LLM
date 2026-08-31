from os import name
import ast
from openai import OpenAI
import wikipedia
from typing import Any , cast
import json
import re
import traceback

wikipedia.set_rate_limiting(True)

def Search(query:str):
    try:
        wikipedia.set_user_agent("finetuneLLM/1.0 (contact@example.com)")
        page = wikipedia.search(query)
        if  page:
            return page
        return None
    except Exception as e :
        print(f"Search Function error type: {type(e).__name__}, details: {e}")
        return None

qwen='qwen2.5-coder:3b'





def Calculator(A:int | float,B:int | float, operator :str):
    match operator:
        case 'add':
            return A+B
        case 'divide' :

            return A/B
        case 'multiply':
            return A*B
        case 'subtraction':
            return A-B
        case _ :
            return 'Invalid operator'


def Search_page(query):
  try :
        wikipedia.set_user_agent("finetuneLLM/1.0 (contact@example.com)")
        page = wikipedia.summary(query,auto_suggest=False)
        if page :
            return page
        return None

  except Exception as e :
      print('error occured at search page ' , e )
      return None


client =OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama'
)


def Agent_Search_Calculate(User_Input):


    answer = client.responses.create(
        model=qwen,
        input=User_Input,
        tools=cast(Any,[
            {
                "name": "Search",
                "type": "function",
                "description": "if you need up to date information you can use this",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "query":{
                        "type":"string"
                        ,"description":"the search query"
                    }}
                }
                ,"required":['query']
            },
            {
                "name": "Calculator",
                "type": "function",
                "description": "Perform basic math calculations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "The math operation to use.",
                        },
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": (
                                "The two numbers to calculate, e.g. [8, 8]"
                            ),
                        },
                    },
                    "required": ["operation", "numbers"],
                },
            },
        ],)
    )


    theoutput=[]
    if not answer.output:
        return 'Error No answer.output'

    for output in answer.output :
        for content in cast(list[str], getattr(output, "content", [])):
            data=None
            text_data :str = getattr(content,'text','')
            if text_data:
                cleaned = text_data.replace("```json", "").replace("```", "").strip()

                cleaned = re.sub(r'}\s*\{', '},{', cleaned)

                final_json_str = "[" + cleaned + "]"

                try:


                        data = json.loads(final_json_str)
                except json.JSONDecodeError:
                    print(final_json_str)
                    print('error ocurred right here ')
                    continue
            if data is None:
                return 'Error occured data is Empty '
            try:
                for content in data :
                    name = content.get('name')
                    arguments = content.get('arguments')

                    match name:
                        case 'Search':
                            query = arguments['query']
                            res = Search(query)
                            if  res is None :
                                return 'Error res is Empty'
                            print('Results are ' , res)

                            summary_strings:list[str]=[]
                            for result in res :
                                summary = Search_page(result)
                                if summary is  None:
                                    print('Summary of pages are Emepty ')
                                summary_strings.append(f'query is : {result} and summary is {summary}')
                            if summary_strings :
                                new_summary_strings : str = ','.join(summary_strings)
                                theoutput.append( { "type": "function_call_output","call_id":cast(list[str],getattr(output, "call_id", [])) ,"output": new_summary_strings})


                        case 'Calculator':

                                        A,B = arguments['numbers']
                                        operation =arguments['operation']
                                        result = Calculator(A,B,operation)
                                        theoutput.append({"type": "function_call_output","call_id":output.id,"output": str(result)})
            except Exception as e :
                    print('error occured , ', e )
                    traceback.print_exc()




    return (theoutput, answer.id, User_Input)





theoutput , id , userinput = Agent_Search_Calculate('who won the recent football worldcup  ? and whats 8/8')
if theoutput == []:
    print('its emptyyyyyyyy')
responses = client.responses.create(
    model= qwen,
    previous_response_id=id   ,
    input =theoutput,
    stream=True
)
for event in responses :
    if  hasattr(event,'delta') and event.delta is not None and getattr(event, "type", None) == "response.output_text.delta":
        print(event.delta , end="",flush=True)
