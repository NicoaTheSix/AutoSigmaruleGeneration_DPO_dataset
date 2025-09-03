import re,os,time,json,random,subprocess,ollama,argparse,pandas as pd
from glob import glob
from tqdm import tqdm
from openai import OpenAI
import settings
import uuid
import argparse
import sys

from settings import home_path,response_title,response_folder_path,targetOS,dir_ttp,dict_ttp,csv_ttp,csv_ttp_noPr,dir_cti,generate_secure_random_string,loadSettings,saveRecord,file_encoding
empty_char=""
"""
Data lookup
"""
def dataLookUp(ID:str="N",type:str="enterprise"):
    data=""
    if ID[0]=="T":
        if ID[1]=="A":
            data="tactics.json"
        else:
            data="techniques_detailed.json"
    elif ID[0]=="S":data="softwares.json"
    elif ID[0]=="G":data="groups.json"
    elif ID[0]=="C":data="campaigns.json"
    elif ID[0]=="A":data="assets.json"
    elif ID[0]=="D":data="datasources.json"
    else: return "Can't find result"

    with open(os.path.join(os.getcwd(),"data",data),"r")as file:
        content=json.load(file)
    
    if ID[0]=="T":return {"ID":content[type][ID]["ID"],
                          "name":content[type][ID]["name"],
                          "description":content[type][ID]["description"]}
    else:return {"ID":content[ID]["ID"],
                "name:":content[ID]["name"],
                "description:":content[ID]["description"]}

"""
funtion: request LLM
"""
def Llmrequest(messages:list=[{"role":"user","content":"nothing to say"}],source:str=settings.source,llm:str=settings.llm):
    """ 
    目前有Openai api與Ollama 套件作為LLM來源
    """
        
    def gpt_request(llm:str="gpt-4o-mini",messages: list=[{"role":"user","content":"nothing to say"}]):
        # Get Response from GPT
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key = api_key)
        response = client.chat.completions.create(
        model = llm,
        messages = messages,
        temperature = 0
        )
        return response.choices[0].message.content
    def ollama_request(llm:str = "llama3.2", messages:list = [{"role":"user","content":"nothing to say"}]):
        response= ollama.chat(
        model=llm,
        messages=messages
        )
        return response['message']['content']
    if source == "openai":
        return gpt_request(llm=llm,messages=messages)
    elif source == "ollama" :
        return ollama_request(llm=llm,messages=messages)
"""
fuction : Load the prompt from thedirectory :Prompt:
"""
def textLoader(txtName:str):
    with open(os.path.join(os.getcwd(),"prompt",txtName),"r",encoding="utf-8")as file:
        prompt=file.read()
    return prompt
"""
function :generate sigma rule
"""
def sigmaruleGeneration(dict_input:dict={},display:bool=False):
    print("[+]Start generating sigma rule.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_sigmaRuleGeneration")
    UserPrompt="<text>"+str(dict_input)+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    sigmarule=Llmrequest(messages)
    print("[-]Finish generating sigma rule.")
    return sigmarule
"""
function    :translate Sigma rule to KQL
"""
def KQLGeneration(input:str="",display:bool=False):
    print("[+]Start generating KQL.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_KQLGeneration")
    UserPrompt="<text>"+input+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    KQL=Llmrequest(messages)
    print("[-]Finish generating KQL.")
    return KQL


def workflow_sigmaRule(dict_input:dict={"higasa":"T1204\tUser Execution\tManual execution by user (opening LNK file)","id":str(uuid.uuid4())}):
    """
    這邊寫生成sigma rule的工作流程
    """
    #生成sigma rule
    sigmarule=sigmaruleGeneration(dict_input=dict_input)
    print(sigmarule)
    count=0
    #微調basic sigma rule
    sigmarule_refined=sigmaruleRefiner(dict_input={"unrefined_rule":sigmarule,"criteria":"detect by keywords but others"})
    print(sigmarule_refined)
    #整合basic sigma rule跟refined detecion rule
    result=sigmaCombination(dict_input={"basic sigma rule":sigmarule,"refined detection rule":sigmarule_refined})
    resultPattern=re.compile(r'<output>(.*?)</output>', re.DOTALL)
    resultContent = resultPattern.findall(result)[0]
    filename=generate_secure_random_string(10)
    with open(os.path.join(os.getcwd(),"response",filename+"_sigmarule.yaml"),"w",encoding=settings.file_encoding)as f:
        f.write(resultContent)
    query=elasticSearchQueryDSLGeneration(resultContent)
    queryPattern=re.compile(r'<output>(.*?)</output>', re.DOTALL) 
    queryContent = queryPattern.findall(query)[0]
    print(queryContent)
    with open(os.path.join(os.getcwd(),"response",filename+"_query.yaml"),"w",encoding=settings.file_encoding)as f:
        f.write(queryContent)
    return queryContent

def sigmaruleRefiner(dict_input:dict={},display:bool=False):
    print("[+]Start refining sigma rule.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_sigmaruleRefiner")
    UserPrompt="<text>"+str(dict_input)+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    sigmarule_refined=Llmrequest(messages)
    print("[-]Finish refining sigma rule.")
    return sigmarule_refined

def sigmaCombination(dict_input:dict={"basic sigma rule":"","refined detection rule":""},display:bool=False):
    print("[+]Start combining sigma rule.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_sigmaCombination")
    UserPrompt="<text>"+str(dict_input)+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    sigmarule_refined=Llmrequest(messages)
    print("[-]Finish combining sigma rule.")
    return sigmarule_refined

def elasticSearchQueryDSLGeneration(input:str="",display:bool=False):
    print("[+]Start generating query.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_queryGeneration")
    UserPrompt="<text>"+input+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    query=Llmrequest(messages)
    print("[-]Finish generating query.")
    return query

def elsticSearch_search(query,index:str="sagac1"):
    cmd = ["curl","-u", "elastic:1eqJXNpXocyu9EHg1*hO","-X", "GET",f"https://localhost:9200/{index}/_search?pretty","-H", "Content-Type: application/json","-d",json.dumps(query),"--insecure"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def workflow_costar_pipeline(ttp_id: str, ttp_description: str, procedure_examples: str, ttp_detection: str):
    print("Executing CO-STAR pipeline")

    # Stage 1
    prompt1 = textLoader("SystemPrompt_stage1_COSTAR.txt").format(ttp_id, ttp_description)
    stage1_output = Llmrequest([{"role": "system", "content": prompt1}])
    print("Stage 1 output:\n", stage1_output)

    # Stage 2
    prompt2 = textLoader("SystemPrompt_stage2_COSTAR.txt").format(ttp_id, ttp_description, procedure_examples, stage1_output)
    stage2_output = Llmrequest([{"role": "system", "content": prompt2}])
    print("Stage 2 output:\n", stage2_output)

    # Stage 3
    prompt3 = textLoader("SystemPrompt_stage3_COSTAR.txt").format(stage2_output)
    stage3_output = Llmrequest([{"role": "system", "content": prompt3}])
    print("Stage 3 output:\n", stage3_output)

    # Stage 4
    prompt4 = textLoader("SystemPrompt_stage4_COSTAR.txt").format(ttp_detection, stage3_output)
    stage4_output = Llmrequest([{"role": "system", "content": prompt4}])
    print("Stage 4 output:\n", stage4_output)

    # Stage 5
    prompt5 = textLoader("SystemPrompt_stage5_COSTAR.txt").format(stage4_output)
    stage5_output = Llmrequest([{"role": "system", "content": prompt5}])
    print("Stage 5 output:\n", stage5_output)

    return stage5_output


def workflow1():
    print("Executing workflow 1")
    # TODO: Add your workflow1 logic here


def workflow2():
    print("Executing workflow 2")
    aaaa=["T1059\tCommand-Line Interface\tStarts CMD.EXE for commands (WinRAR.exe, wscript.exe) execution","T1106\tExecution through API\tApplication (AcroRd32.exe) launched itself","T1053\tScheduled Task\tLoads the Task Scheduler DLL interface (Officeupdate.exe)","T1064\tScripting\tExecutes scripts (34fDFkfSD38.js)","T1204\tUser Execution\tManual execution by user (opening LNK file)","Persistence\tT1060\tRegistry Run Keys / Startup Folder\tWrites to a start menu file (Officeupdate.exe)","T1053\tScheduled Task\tUses Task Scheduler to run other applications (Officeupdate.exe)","Privilege Escalation\tT1053\tScheduled Task\tUses Task Scheduler to run other applications (Officeupdate.exe)","Defense Evasion\tT1064\tScripting\tExecutes scripts (34fDFkfSD38.js)","T1140\tDeobfuscate/Decode Files or Information\tcertutil to decode Base64 binaries, expand.exe to decompress a CAB file","Discovery\tT1012\tQuery Registry\tReads the machine GUID from the registry","T1082\tSystem Information Discovery\tReads the machine GUID from the registry","T1016\tSystem Network Configuration Discovery\tUses IPCONFIG.EXE to discover IP address"]
    descriptionFromSaga=[
    "T1547.001\tBoot or Logon Autostart Execution - Registry Run Keys/Startup Folder\tCreates startup shortcut (sllauncherENU.dll (copy).lnk) via cscript.exe execution",
    "T1547.001\tBoot or Logon Autostart Execution - Registry Run Keys/Startup Folder\tCreates startup shortcut (sllauncherENU.dll (copy).lnk) via cscript.exe execution",
    "T1547.001\tBoot or Logon Autostart Execution - Registry Run Keys/Startup Folder\tQueries shortcut file information (sllauncherENU.dll (copy).lnk) using cscript.exe",
    "T1547.001\tBoot or Logon Autostart Execution - Registry Run Keys/Startup Folder\tWrites data to shortcut file (sllauncherENU.dll (copy).lnk) using cscript.exe",
    "T1547.001\tBoot or Logon Autostart Execution - Registry Run Keys/Startup Folder\tCloses shortcut file handle (sllauncherENU.dll (copy).lnk) using cscript.exe",#
    "T1082\tSystem Information Discovery\tUses PowerShell.exe ($PSVersionTable) to gather system information (created by cscript.exe executing Retrive4075693065230196915.vbs)",#
    "T1016\tSystem Network Configuration Discovery\tUses ipconfig.exe to discover IP address",
    "T1059\tScripting\tExecutes script using cscript.exe (Retrive4075693065230196915.vbs)",#
    "T1036.004\tMasquerading: Masquerade Task or Service\tUses sc.exe to create a service pointing to 'sllauncherENU.dll (copy)'",#
    "T1053.005\tScheduled Task\tUses SCHTASKS.EXE to create a task that runs sllauncherENU.dll (copy)",
    "T1064\tScripting\tExecutes script using cscript.exe (Retrive4075693065230196915.vbs)",#
    "T1204.002\tUser Execution\tcmd.exe created and executed Retrive4075693065230196915.vbs (CreateFile)",
    "T1204.002\tUser Execution\tcmd.exe queried basic information of Retrive4075693065230196915.vbs (QueryBasicInformationFile)",
    "T1204.002\tUser Execution\tcmd.exe wrote to Retrive4075693065230196915.vbs (WriteFile)",
    "T1204.002\tUser Execution\tcmd.exe closed Retrive4075693065230196915.vbs (CloseFile)",
    "T1204.002\tUser Execution\tcscript.exe executed Retrive4075693065230196915.vbs (Process Create)",
    "T1204.002\tUser Execution\tWINWORD.EXE triggered rFupMb75.exe (CreateFile)",
    "T1204.002\tUser Execution\tcmd.exe launched WINWORD.EXE via DDE (Process Create)"]
    for i in aaaa:
        print(i)
        dict_input={"higasa":i}
        query=workflow_sigmaRule(dict_input=dict_input)
        print(elsticSearch_search(query))

    # TODO: Add your workflow2 logic here


def workflow3():
    print("Executing workflow 3")
    # TODO: Add your workflow3 logic here
    with open(os.path.join(os.getcwd(),"response","VbGfW2bLcK_sigmarule.yml"),"r",encoding='utf-8')as f:
        resultContent=f .read()
    query=elasticSearchQueryDSLGeneration(resultContent)
    print(query)
    print(elsticSearch_search(query))
    return
def workflow4():
    print("Executing workflow 4")
    with open(os.path.join(os.getcwd(),"response","test.yml"),"r",encoding='utf-8')as f:
        Content=f .read()
    print(KQLGeneration(Content))
    # TODO: Add your workflow4 logic here


def workflow5():
    print("Executing workflow 5")
    """    # TODO: Add your workflow5 logic here
    for i in os.listdir(os.path.join(os.getcwd(),"SAGA_RULE")):
        dir_=i
        for j in os.listdir(os.path.join(os.getcwd(),"SAGA_RULE",i)):
            dir__=j
            for k in os.listdir(os.path.join(os.getcwd(),"SAGA_RULE",i,j)):
                #print(i)
                if not k.endswith("txt"):
                    with open(os.path.join(os.getcwd(),"SAGA_RULE",i,j,k),"r",encoding='utf-8')as f:
                        Content=f.read()
                    query_KQL=KQLGeneration(Content)
                    queryPattern=re.compile(r'<output>(.*?)</output>', re.DOTALL) 
                    queryContent = queryPattern.findall(query_KQL)[0]
                    file_name=i+"_"+j+"_"+k.split(".")[0]+"_KQLquery.txt"
                    print(f"[+]Save as {file_name}")
                    with open(os.path.join(os.getcwd(),"response",file_name),"w",encoding='utf-8')as f:
                        f.write(queryContent)"""
        #print(KQLGeneration(Content))
            # TODO: Add your workflow5 logic her
    for k in os.listdir(os.path.join(os.getcwd(),"txt")):
        #print(i)
        if not k.endswith("txt"):
            with open(os.path.join(os.getcwd(),"txt",k),"r",encoding='utf-8')as f:
                Content=f.read()
            query_KQL=KQLGeneration(Content)
            queryPattern=re.compile(r'<output>(.*?)</output>', re.DOTALL) 
            queryContent = queryPattern.findall(query_KQL)[0]
            file_name="_"+"_"+k+"_KQLquery.txt"
            print(f"[+]Save as {file_name}")
            with open(os.path.join(os.getcwd(),"response",file_name),"w",encoding='utf-8')as f:
                f.write(queryContent)
    

def workflow6():
    print("Executing workflow 6")
    # TODO: Add your workflow6 logic here


def workflow7():
    print("Executing workflow 7")
    # TODO: Add your workflow7 logic here


def workflow8():
    print("Executing workflow 8")
    # TODO: Add your workflow8 logic here


def workflow9():
    print("Executing workflow 9")
    # TODO: Add your workflow9 logic here


def workflow10():
    print("Executing workflow 10")
    # TODO: Add your workflow10 logic here


# Mapping of input choices to workflow functions
WORKFLOWS = {
    '1': workflow1,
    '2': workflow2,
    '3': workflow3,
    '4': workflow4,
    '5': workflow5,
    '6': workflow6,
    '7': workflow7,
    '8': workflow8,
    '9': workflow9,
    '10': workflow10,
    'costar': workflow_costar_pipeline,
}

def main():
    parser = argparse.ArgumentParser(
        description='CLI to execute predefined workflows.'
    )
    parser.add_argument(
        'workflow',
        choices=WORKFLOWS.keys(),
        help='Workflow to execute'
    )
    # Add arguments for the new pipeline
    parser.add_argument('--ttp-id', help='TTP ID for CO-STAR pipeline')
    parser.add_argument('--ttp-description', help='TTP description for CO-STAR pipeline')
    parser.add_argument('--procedure-examples', help='Procedure examples for CO-STAR pipeline')
    parser.add_argument('--ttp-detection', help='TTP detection methods for CO-STAR pipeline')

    args = parser.parse_args()

    # Execute the selected workflow
    func = WORKFLOWS[args.workflow]

    if args.workflow == 'costar':
        if not all([args.ttp_id, args.ttp_description, args.procedure_examples, args.ttp_detection]):
            print("Error: --ttp-id, --ttp-description, --procedure-examples, and --ttp-detection are required for the costar pipeline.")
            sys.exit(1)
        func(args.ttp_id, args.ttp_description, args.procedure_examples, args.ttp_detection)
    else:
        func()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # No arguments provided, show help
        print("Please specify a workflow to execute.\n")
        parser = argparse.ArgumentParser(
            description='CLI to execute predefined workflows.'
        )
        parser.print_help()
        sys.exit(1)

    main()