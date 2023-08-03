# -*- coding: UTF-8 -*-

import streamlit as st
import os
import re
import openai
import io
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from importlib import reload
from . import utils #relative import
utils = reload(utils)

# Define the Streamlit app
def main():

    pkg_path = utils.pkg_path
    filename = re.findall('(.*).py', os.path.basename(__file__)) #仅包括扩展名前的部分
    utils.errorLog(pkg_path,filename)

    openai_apikey  = utils.loadJSON(json_name='openaiapi')['key']
    os.environ['OPENAI_API_KEY'] = openai_apikey
    openai.api_key = openai_apikey
    
    # Paste your API Key below.
    stabilityai_apikey  = utils.loadJSON(json_name='stabilityaiapi')['key']
    os.environ['STABILITY_KEY'] = stabilityai_apikey

    st.title('Image Generator App')

    # Initialize session state if it doesn't exist
    if 'prompts' not in st.session_state:
        st.session_state['prompts'] = []
    if 'selected_prompt' not in st.session_state:
        st.session_state['selected_prompt'] = ""
    if 'edited_prompt' not in st.session_state:
        st.session_state['edited_prompt'] = ""

    # Input text field for user to type their description
    description = st.text_input(r'简单描述一下你想要生成什么样的照片、图片:')


    def generatePromptViaOpenaiAPI():
        # Here is where you would send a request to the GPT API with the user's description
        def callOpenaiAPI(model="gpt-4"):
            response = openai.ChatCompletion.create(
            model=model,  #"gpt-3.5-turbo",
            messages=[
                {"role": "user", 
                "content": r"Please write a comprehensive prompt in English based on below descriptions in order to generate a high quality realistic photograph. The prompt should include the photo's resolution details. Please provide two prompts." + description}, # Please generate three options.
                ])
            prompts = response['choices'][0]['message']['content']
            return prompts
            
        option_1 = callOpenaiAPI(model="gpt-4")
        option_2 = callOpenaiAPI(model="gpt-4")
        #st.write(prompts)
        st.session_state['prompts'] = [option_1, option_2]
        # Display the prompts to the user and allow them to select one
        #selected_prompt = st.selectbox('Select a prompt:', [prompts])
        st.session_state['selected_prompt'] = st.selectbox(r'提示语已生成，请任选一个:', st.session_state['prompts'])
        
        # Allow the user to edit the selected prompt
        #edited_prompt = st.text_input('Edit the selected prompt if necessary:', value=selected_prompt)
        #edited_prompt = st.text_input('Edit the selected prompt if necessary:', value=st.session_state['selected_prompt'])
        

        #if st.session_state['selected_prompt']:
        st.session_state['edited_prompt'] = st.text_input(r'如有需要，可在此处编辑提示语:', value=st.session_state['selected_prompt'])



    def generateImageViaStabilityai(prompt):
        # Here is where you would send a request to the Stability.ai API with the user's edited prompt
        # Our Host URL should not be prepended with "https" nor should it have a trailing slash.
        os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

        # Sign up for an account at the following link to get an API Key.
        # https://platform.stability.ai/

        # Click on the following link once you have created an account to be taken to your API Key.
        # https://platform.stability.ai/account/keys
            
        # Set up our connection to the API.
        stability_api = client.StabilityInference(
            key=os.environ['STABILITY_KEY'], # API Key reference.
            verbose=True, # Print debug messages.
            engine="stable-diffusion-xl-1024-v1-0", # Set the engine to use for generation.
            # Check out the following link for a list of available engines: https://platform.stability.ai/docs/features/api-parameters#engine
        )
        
        # Set up our initial generation parameters.
        answers = stability_api.generate(
            prompt=prompt,
            seed=4253978046, # If a seed is provided, the resulting generated image will be deterministic.
                            # What this means is that as long as all generation parameters remain the same, you can always recall the same image simply by generating it again.
                            # Note: This isn't quite the case for Clip Guided generations, which we'll tackle in a future example notebook.
            steps=50, # Amount of inference steps performed on image generation. Defaults to 30. 
            cfg_scale=8.0, # Influences how strongly your generation is guided to match your prompt.
                        # Setting this value higher increases the strength in which it tries to match your prompt.
                        # Defaults to 7.0 if not specified.
            width=1024, # Generation width, defaults to 512 if not included.
            height=1024, # Generation height, defaults to 512 if not included.
            samples=1, # Number of images to generate, defaults to 1 if not included.
            sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                        # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
                                                        # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
        )

        # Set up our warning to print to the console if the adult content classifier is tripped.
        # If adult content classifier is not tripped, save generated images.
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    warnings.warn(
                        "Your request activated the API's safety filters and could not be processed."
                        "Please modify the prompt and try again.")
                if artifact.type == generation.ARTIFACT_IMAGE:
                    img = Image.open(io.BytesIO(artifact.binary))
                    #img.save(str(artifact.seed)+ ".png") # Save our generated images with their seed number as the filename.
                    st.image(img, caption=f'Seed {artifact.seed}', use_column_width=True)



    # Button to generate prompts
    if st.button(r'生成提示语'):
        generatePromptViaOpenaiAPI()
        st.session_state['prompt_generated'] = True

        # Button to generate the image
        #if st.button('Generate Image'):
        #    generateImageViaStabilityai(prompt=st.session_state['selected_prompt'])
            


    # Button to generate the image
    #if st.session_state.get('prompt_generated', False) or st.button('Generate Image'):
    if st.button(r'生成图片'):
        generateImageViaStabilityai(prompt=st.session_state['edited_prompt'])
        st.session_state['prompt_generated'] = False