from os import name
import ast
from openai import OpenAI
import wikipedia
def Search(query:str):
    page = wikipedia.search(query)
    if  page:
         return page
    return 'Page not found'



def Search_page(query):
  page = wikipedia.summary(query,auto_suggest=False)
  if page :
    return page
  return None


def Calculator(A:int | float,B:int | float, operator :str):
    match operator:
        case '+':
            return A+B
        case '/' :

            return A/B
        case '*':
            return A*B
        case '-':
            return A-B
        case _ :
            return 'Invalid operator'


client =OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama'
)

answer = client.responses.create(
    model="qwen2.5:7b",
    input="Who is the current president of albania ?",
    tools=[{"name":"Search", "type": "Search"},{"type":"Calculator"}]  # type: ignore
)

if answer.output[0].arguments:
  asn = answer.output[0].arguments
  query = ast.literal_eval(asn)
  query = query['query']
  res = Search(query)
  summary_strings=[]
  for result in res :
    print(result)
    summary = Search_page(result)
    if summary is not None:
      summary_strings.append(f'query is : {result} and summary is {summary}')
  summary_strings= ','.join(summary_strings)
