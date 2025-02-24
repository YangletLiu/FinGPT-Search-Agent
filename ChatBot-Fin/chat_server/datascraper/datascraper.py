from dotenv import load_dotenv
import time
import requests
from bs4 import BeautifulSoup
import os
import openai
from googlesearch import search
from urllib.parse import urljoin
# from transformers import AutoTokenizer, AutoModelForCausalLM
# from accelerate import init_empty_weights, load_checkpoint_and_dispatch
# import torch
from . import cdm_rag

load_dotenv()
api_key = os.getenv("API_KEY7")


def data_scrape(url, timeout=2):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        elapsed_time = end_time - start_time

        if response.status_code == 200:
            print("Successful response: ", url)
            if elapsed_time > timeout:
                print("Request took more than 2 seconds. Skipping: ", url)
                return -1
            soup = BeautifulSoup(response.text, 'html.parser')
            first_5000_characters = soup.text[:5000]

            return first_5000_characters
        else:
            print('Failed to retrieve the page: ', url)
            return -1
    except requests.exceptions.Timeout:
        print('Request timed out after', timeout, 'seconds. Skipping: ', url)
        return -1
    except Exception as e:
        print('An error occurred:', str(e))
        return -1


def get_preferred_urls():
    """
    Reads user-preferred URLs from a file and returns them as a list.
    """
    file_path = 'preferred_urls.txt'
    preferred_urls = []

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            preferred_urls = [line.strip() for line in file.readlines()]

    return preferred_urls


def search_preferred_urls(keyword):
    """
    Searches within the preferred URLs using the provided keyword.
    """
    preferred_urls = get_preferred_urls()
    message_list = []

    for url in preferred_urls:
        info = data_scrape(url)
        print(f"Found in preferred URL: {url}")
        message_list.append({"role": "system", "content": info})
        # if info != -1 and keyword.lower() in info.lower():
        #     print(f"Found in preferred URL: {url}")
        #     message_list.append({"role": "system", "content": info})
        # else:
        #     print(f"Nothing found in preferred URL: {url}")

    return message_list


def search_websites_with_keyword(keyword):
    """
    Searches the web using Google and prioritizes user-preferred URLs.
    """
    # First, search within preferred URLs
    message_list = search_preferred_urls(keyword)

    # If no relevant information found in preferred URLs, fall back to Google search
    if not message_list:
        search_query = f"intitle:{keyword}"
        search_url = f"https://www.google.com/search?q={search_query}"
        headers = {"User-Agent": "Your User Agent Here"}
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            search_results = soup.find_all("a")
            for result in search_results:
                link = result.get("href")
                if link and link.startswith("/url?q="):
                    url = link[7:]
                    info = data_scrape(url)
                    if info != -1:
                        message_list.append({"role": "system", "content": info})
        else:
            print("Failed to retrieve search results.")

    return message_list

def create_rag_response(user_input, message_list, model):
    """
    Generates a response using the RAG pipeline.
    """
    try:
        response = cdm_rag.get_rag_response(user_input, model)
        message_list.append({"role": "system", "content": response})
        return response
    except FileNotFoundError as e:
        # Handle the error and return the error message
        error_message = str(e)
        message_list.append({"role": "system", "content": error_message})
        return error_message

def create_rag_advanced_response(user_input, message_list, model):
    """
    Generates an advanced response using the RAG pipeline.
    """
    try:
        response = cdm_rag.get_rag_advanced_response(user_input, model)
        message_list.append({"role": "system", "content": response})
        return response
    except FileNotFoundError as e:
        # Handle the error and return the error message
        error_message = str(e)
        message_list.append({"role": "system", "content": error_message})
        return error_message



# gemma_model_path = os.path.join(os.path.dirname(__file__), 'gemma-2-2b-it')
# tokenizer = AutoTokenizer.from_pretrained(gemma_model_path)
#
# # Initialization
# with init_empty_weights():
#     model = AutoModelForCausalLM.from_pretrained(
#         gemma_model_path,
#         low_cpu_mem_usage=True,
#         torch_dtype=torch.bfloat16  # model weights use bfloat16
#     )
#
# # tie the model weights before dispatching
# model.tie_weights()
#
# # Load the model with CPU offloading and layer dispatch to handle limited memory
# model = load_checkpoint_and_dispatch(
#     model,
#     gemma_model_path,
#     device_map={"": "cpu"},
#     offload_state_dict=True
# )


# Gemma 2B - Modified response generation to work on CPU
# def generate_gemma_response(message_list):
#     # concatenated_input = " ".join([msg["content"] for msg in message_list])
#     #
#     # print(concatenated_input)
#     #
#     # # keep input_ids as LongTensor
#     # inputs = tokenizer(concatenated_input, return_tensors="pt")
#     # inputs = {key: value.to("cpu") for key, value in inputs.items()}
#     #
#     # # model weights are in bfloat16
#     # outputs = model.generate(**inputs, max_length=6000)
#     #
#     # # Decode the generated output
#     # full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
#     #
#     # print("Output prior to stripping: " + full_output)
#     full_output = "This is a mock output."
#
#     # response = full_output.replace(concatenated_input, "").strip()
#
#     return full_output
#
#
# # Gemma 2B
# def create_gemma_response(user_input, message_list):
#     """
#     Generates a response from the locally run Gemma 2B model.
#     """
#
#     message_list.append({"role": "user", "content": user_input})
#
#     print("The received message list for response generation:", message_list)
#
#     response = generate_gemma_response(message_list)
#     message_list.append({"role": "system", "content": response})
#
#     print(response)
#     return response
#
#
# # Gemma 2B
# def create_gemma_advanced_response(user_input, message_list):
#     """
#     Generates an advanced response from the locally run Gemma 2B model,
#     searching URLs before generating a response.
#     """
#
#     message_list.append({"role": "user",
#                          "content": "Answer the following question with the context provided below: " + user_input + "\n" + "Below is context: " + "\n"})
#
#     # Search in preferred URLs first
#     print("Searching user preferred URLs")
#     preferred_message_list = search_preferred_urls(user_input)  # URL searching logic
#     message_list.extend(preferred_message_list)
#
#     # If no relevant information found, fall back to Gemma 2B response
#     if not preferred_message_list:
#         for url in search(user_input, num=10, stop=10, pause=0):
#             info = data_scrape(url)
#             if info != -1:
#                 message_list.append({"role": "system", "content": "url: " + str(url) + " info: " + info})
#
#     print(message_list)
#     response = generate_gemma_response(message_list)
#
#     message_list.append({"role": "system", "content": response})
#
#     return response


def create_response(user_input, message_list, model="o1-preview"):
    """
    Creates a response using OpenAI's API and a specified model.
    """
    def create_response(user_input, message_list, model="o1-preview"):
        """
        Creates a response using either OpenAI's ChatCompletion or the Deepseek
        API, depending on the 'model' argument.
        """

    # If the user selected "o1-preview" or "gpt-4o", we stick with standard openai
    # If "deepseek-R1" is chosen, we call the Deepseek client
    if model == "deepseek-reasoner":
        # Deepseek logic
        from openai import OpenAI
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")

        client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"  # can use https://api.deepseek.com/v1
        )

        # The "system" prompt in Deepseek is optional, but we can keep it for consistency
        # Filter out 'system' role if needed, or adapt them. For now, we assume it is fine:
        filtered_message_list = [msg for msg in message_list if msg["role"] != "system"]
        filtered_message_list.append({"role": "user", "content": user_input})

        # Convert message_list to the shape Deepseek needs
        # Usually: messages=[{"role": "system", "content": ...}, {"role": "user", "content": ...}]
        # We'll just assume it’s the same shape as OpenAI
        response = client.chat.completions.create(
            model="deepseek-reasoner",  # This is the actual model name on their side
            messages=filtered_message_list
        )
        return response.choices[0].message.content

    else:
        # For o1-preview or gpt-4o, do the usual OpenAI call
        openai.api_key = api_key

        # Filter out 'system' role messages if the model does not support them
        filtered_message_list = [msg for msg in message_list if msg["role"] != "system"]
        filtered_message_list.append({"role": "user", "content": user_input})

        completion = openai.ChatCompletion.create(
            model=model,
            messages=filtered_message_list,
        )
        return completion.choices[0].message.content




def create_advanced_response(user_input, message_list, model="o1-preview"):
    """
    Creates an advanced response by searching through user-preferred URLs first,
    and then falling back to a general web search using the specified model.
    """
    print(message_list)
    openai.api_key = api_key
    print("starting creation")

    # Search in preferred URLs first
    print("Searching user preferred URLs")
    preferred_message_list = search_preferred_urls(user_input)
    message_list.extend(preferred_message_list)

    # If no relevant information found, fall back to general web search
    if not preferred_message_list:
        for url in search(user_input, num=10, stop=10, pause=0):
            info = data_scrape(url)
            if info != -1:
                message_list.append({"role": "system", "content": "url: " + str(url) + " info: " + info})

    message_list.append({"role": "user", "content": user_input})
    completion = openai.ChatCompletion.create(
        model=model,
        messages=message_list,
    )
    print(completion.choices[0].message.content)

    return completion.choices[0].message.content


def get_sources(query):
    """
    Retrieves source URLs by first searching through preferred URLs, then falling back to Google search.
    """
    sources = []

    # First, search within preferred URLs
    preferred_urls = get_preferred_urls()
    for url in preferred_urls:
        info = data_scrape(url)
        if info != -1 and query.lower() in info.lower():
            tup = url, get_website_icon(url)
            sources.append(tup)
            print(f"Preferred source: {url}")

    # If no sources found in preferred URLs, fall back to Google search
    if not sources:
        for url in search(query, num=6, stop=6, pause=0):
            info = data_scrape(url)
            if info != -1:
                tup = url, get_website_icon(url)
                sources.append(tup)
                print(url)

    return sources


def get_website_icon(url):
    """
    Retrieves the website icon (favicon) for a given URL.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    favicon_tag = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
    if favicon_tag:
        favicon_url = favicon_tag.get('href')
        favicon_url = urljoin(url, favicon_url)
        return favicon_url
    return None


def handle_multiple_models(question, message_list, models):
    """
    Handles responses from multiple models and returns a dictionary with model names as keys.
    """
    responses = {}
    for model in models:
        if "advanced" in model:
            responses[model] = create_advanced_response(question, message_list.copy(), model)
        else:
            responses[model] = create_response(question, message_list.copy(), model)
    return responses
