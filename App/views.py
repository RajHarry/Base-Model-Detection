from django.shortcuts import render
from App.models import DynamicUpload
from django.http import JsonResponse
import glob
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import cv2
from django.shortcuts import render
import time
import base64
import numpy as np
import os,io,re
from FaceMaskDetection.ssd_opencv import inference
import requests
from PIL import Image
import json
import datetime

def get_current_time():
    e = datetime.datetime.now()
    return str(e.day)+"_"+str(e.month)+"_"+str(e.year)+"_"+str(e.hour)+"_"+str(e.minute)+"_"+str(e.second)

def index(request):
    static_images = glob.glob("media/static-img/*")
    img_names, img_ids, funcs, img_urls = [], [], [], []
    for id, image_file in enumerate(static_images):
        img_names.append(image_file.split("/")[-1])
        img_urls.append(image_file)
        img_ids.append("im_click_id_"+str(int(id)+1))
        funcs.append(f"imageClick({int(id)+1})")
    return render(request, 'index.html', {'data': zip(img_names, img_ids, funcs, img_urls)})

def image_details_bk(request):
    response_data = {}
    #print(request.FILES)
    browse_image = request.FILES['browse_image']
    #print(browse_image)
    file_name = str(browse_image).replace(" ", "_").replace("&", "")
    model = DynamicUpload(image=browse_image, name=file_name)
    model.save()
    response_data['file_name'] = file_name
    response_data['image_url'] = "media/dynamic/"+file_name
    return JsonResponse(response_data)

def remove_symbols(file_name):
    return str(re.sub(r'[^\w]', '', file_name))

def _grab_image(path=None, stream=None, url=None):
        # if the path is not None, then load the image from disk
        if path is not None:
                image = cv2.imread(path)
        # otherwise, the image does not reside on disk
        else:   
                # if the URL is not None, then download the image
                if url is not None:
                        resp = urllib.urlopen(url)
                        data = resp.read()
                # if the stream is not None, then the image has been uploaded
                elif stream is not None:
                        data = stream.read()
                # convert the image to a NumPy array and then read it into
                # OpenCV format
                image = np.asarray(bytearray(data), dtype="uint8")
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    # return the image
        return image

@csrf_exempt
def model_process(request):
        data = {"success": False}
        # print("request: ",request.method, request.body)
        # if request.method == 'GET':
        st = time.time()
        base64_img = request.POST.get("image", None)
        
        base64_head_replaced = base64_img.replace("data:image/jpeg;base64,","")
        decoded_image = base64.b64decode(str(base64_head_replaced))       
        nparr = np.fromstring(decoded_image, np.uint8)
        image = cv2.imdecode(nparr, cv2.COLOR_BGR2RGB)

        #img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        output_info, img_output,image = inference(image, draw_result=True, target_shape=(260, 260))
        cv2.imwrite("cv2_image_recorded.jpg",image)
        # base64_encoded = base64.b64encode(image)
        with open('cv2_image_recorded.jpg', 'rb') as imageFile:
            str_en = "data:image/jpeg;base64,"+str(base64.b64encode(imageFile.read())).replace("b'","")[:-1]
        #print(str_en)
        #print(base64_encoded)
        data = [{'success':True,'encoded_image':str(str_en),"decoded_image":str(base64_img)}]#'face':image.tolist(),'embedding':embedding.tolist()}]
        # else:
                       #       print("else block")
        return JsonResponse(data,safe=False)

@csrf_exempt
def model_process_image_bk(request):
    print("Model Used: ",request.POST.get("model"))
    data = [{"success": False}]
    # check to see if this is a post request
    if request.method == "POST":
        print("in")
        # check to see if an image was uploaded
        if request.FILES.get("image", None) is not None:
            # grab the uploaded image
            image = _grab_image(stream=request.FILES["image"])
        # otherwise, assume that a URL was passed in
        else:
            # grab the URL from the request
            url = request.POST.get("url", None)
            # if the URL is None, then return an error
            if url is None:
                    data["error"] = "No URL provided."
                    return JsonResponse(data)
            # load the image and convert
            image = _grab_image(url=url)
        if(request.POST.get('model') == "SSD"):
                print(">>>")
                output_info, img_output,out_image = inference(image, draw_result=True, target_shape=(260, 260))
        elif(request.POST.get('model') == "YOLO"):
                out_image = yolo_image_process(image)
        else:
                print("Something is Wring>>")
        # base64_encoded = base64.b64encode(image)
        cv2.imwrite("cv2_image_recorded.jpg",out_image)
        with open('cv2_image_recorded.jpg', 'rb') as imageFile:
            str_en = "data:image/jpeg;base64,"+str(base64.b64encode(imageFile.read())).replace("b'","")[:-1]
        #print(str_en)
        #print(base64_encoded)
        data = [{'success':True,'encoded_image':str(str_en)}]
        # else:
        #       print("else block")
    return JsonResponse(data,safe=False)



def model_process_image(path,model):
    image = cv2.imread(path)
    if(model == "SSD"):
        output_info, img_output,out_image = inference(image, draw_result=True, target_shape=(260, 260))
    elif(model == "YOLO"):
        out_image = yolo_image_process(image)
    else:
        print("Something is Wring>>")
    # base64_encoded = base64.b64encode(image)
    image_path = "media/results/"+path.split("/")[-1]
    cv2.imwrite(image_path,out_image)
    
    return image_path
@csrf_exempt
def image_details(request):
    response_data = {}
    print("request.post: ",request.POST['model'])
    if(request.POST.get('static') == "yes"):
        image_path = "media/static-img/Image"+request.POST['number']+".jpeg"
    else: 
        browse_image = request.FILES['browse_image']
        name,ext = str(browse_image).split(".")
        file_name = get_current_time()+"."+ext

        model = DynamicUpload(image=browse_image, name= str(file_name))
        model.save()

        obj = DynamicUpload.objects.get(name=file_name)
        image_path = "media/"+obj.image.name
    print("Image Path: ",image_path)
    # url = "model_process_image"
    # payload = {"image": open(dynamic_image_path, "rb")}
    # r = requests.post(url, files=payload,data={"model":"SSD"},verify=False).json()
    result_image_stored_path = model_process_image(image_path,"SSD")

    response_data['image_url'] = result_image_stored_path
    return JsonResponse(response_data)