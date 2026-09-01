from os import name
import ast
from openai import OpenAI
import wikipedia
from typing import Any , cast
import json
import re
import traceback
qwen='qwen2.5-coder:3b'
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
    instruction = """ You are an assistant with access to two tools.

    Use Search ONLY when the user asks for information that:
    - is current, recent, or time-sensitive
    - may have changed since your knowledge cutoff
    - explicitly requires searching the web/Wikipedia/news
    - asks about current events, current people in positions, latest results, today's information, etc.

    DO NOT use Search for:
    - greetings
    - casual conversation
    - simple explanations
    - general knowledge that does not require current information

    Use Calculator ONLY when an actual numerical calculation is required.

    If no tool is necessary, answer the user directly."""

    responses = client.responses.create(
        model=qwen,
        instructions=instruction
,        input=User_Input,
        tools=cast(Any,[
            {
                "name": "Search",
                "type": "function",
                "description": "Search the web for information that must be current or recently updated. Use this tool for current events, latest news, current office holders, recent sports results, today's information, or facts that may have changed. Do not use this tool for greetings, casual conversation, or stable general knowledge.",
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
                "description": "Use this tool only when the user asks you to perform a numerical calculation. Do not use it for general reasoning or questions that don't require arithmetic.",
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
        ],),
    )

    while True:
        print(responses.output)
        theoutput=[]
        if not responses.output:
            return 'Error No answer.output'
            for output in responses.output :
                    for content in cast(list[str], getattr(output, "content", [])):
                        data=None
                        if not content :
                            continue
                        text_data :str = getattr(content,'text','')
                        if text_data:
                            cleaned = text_data.replace("```json", "").replace("```", "").strip()

                            cleaned = re.sub(r'}\s*\{', '},{', cleaned)

                            final_json_str = "[" + cleaned + "]"

                            try:


                                    data = json.loads(final_json_str)
                            except json.JSONDecodeError:
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



        if not theoutput:
            return responses.output_text

        responses = client.responses.create(
            model= qwen,
            previous_response_id=responses.id   ,
            input =theoutput,

        )



Agent_Search_Calculate('hello ')
