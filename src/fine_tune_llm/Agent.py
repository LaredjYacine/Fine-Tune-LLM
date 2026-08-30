from os import name

from openai import OpenAI
import wikipediaapi

async def Search(input:str):
    wiki = wikipediaapi.AsyncWikipedia(user_agent='MyProjectName (merlin@example.com)', language='en')
    page= wiki.page(f'{input}')
    if await page.exists():
        summary = await page.summary
        return summary
    return 'Page not found'


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

completion = client.chat.completions.create(
    model='qwen2.5:7b',
    messages=[
        {
        'role':'system','content':'You are a helpful assistant you will use The Functions if you need up to date information '
        },
        {
            'role':'user','content':'Who is the current president of algeria of 2026'        }
    ],
    functions=[
        {
            "name": "Search",
            "description":"Search wikipedia for up to date information and current news or facts",
            "parameters" :{
                "type": "object",
                "properties":{"query":{"type":"string"}},
                "required": ["query"]
            }
        },
        {
            "name":"Calculator",
            "description":"Calculator for simple calculations",
            "parameters":{
                "type":"object",
                "properties":
                    {
                        'A':{"type":"number", "description":"The first number"},
                        'B':{"type":"number", "description":"The secondnumber"}
                        ,'operator':{
                            'type':'string',
                            'enum':["+",'-','/','*'],
                            'description':"the math operations to perform ",
                        }
                    }

            , "required":['A','B','operator']
            }

        }
    ]

)
print(response.choices[0].message.content)
