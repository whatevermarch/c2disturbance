import os
import urllib.request
from PIL import Image

WordNet_ID_page = urllib.request.urlopen('http://www.image-net.org/api/text/imagenet.synset.obtain_synset_list')
WordNet_ID_list = []
URLs_list = []


# get the WordNet_ID page and create the WordNet_ID list
def getWNIDPage():
    for line in WordNet_ID_page:
        decoded_line = line.decode("utf-8").strip()
        if len(decoded_line) > 5:
            WordNet_ID_list.append(decoded_line)
    print("Successfully created the WordNet_ID list which contains elements : {} ".format(len(WordNet_ID_list)))


# create the URLs list from a one WordNet_ID page
def createURLsList(word_net_id):
    imagenet_api_wnid_to_urls = lambda \
            wnid: f'http://www.image-net.org/api/text/imagenet.synset.geturls?wnid={word_net_id}'
    wnid_to_urls_page = urllib.request.urlopen(imagenet_api_wnid_to_urls(word_net_id))  # to resolve the links
    for line in wnid_to_urls_page:
        decoded_line = line.decode("utf-8")
        if len(decoded_line) > 3:
            URLs_list.append(decoded_line)
    print("Successfully fetched {} links from the '{}' WordNet_ID".format(len(URLs_list), word_net_id))


# verify that the image is valid and returns the resolution
def verifyImage(img_name, path):
    img = Image.open(path + img_name)  # open the image file
    width, height = img.size
    img.verify()  # verify that it is, in fact an image
    # print('Image is valid')
    return width, height


# resize the image resolution to (224,224)
def resizeImage(img_name, path):
    img = Image.open(path + img_name)  # open the image file
    new_image = img.resize((224, 224))
    new_image.save(path + img_name)
    # print("image is resized")


# delete image if corrupted or if the resolution is too small
def deleteImage(img_name, path):
    os.remove(path + img_name)  # delete corrupted images
    # print("corrupted image is deleted")


# create or complete the path if its not exist
def createFolder(path):
    if not os.path.isdir(path):
        os.makedirs(path)
        print("The directory: {} is successfully created".format(path))


# to download a specific number of images
def downloadSamples(num_downloaded_img, output_path):
    output_path = output_path + '/'  # to assure saving the images in the specific folder
    createFolder(output_path)  # call createFolder() to create '../../data/samples' output folder path
    valid_images = 0  # indication for valid images
    invalid_images = 0  # indication for invalid images
    invalid_links = 0  # indication for invalid links
    low_resolution_image = 0  # indication for low resolution images
    itercounter = 0  # indication for the loop
    while WordNet_ID_list:
        if valid_images > num_downloaded_img - 1:  # after reaching the number of required image quit the function
            print(valid_images, "Valid images with size (224,224) saved ,", invalid_images,
                  'Invalid images deleted ,', invalid_links, "Invalid Links", low_resolution_image,
                  " low resolution image deleted")
            break
        if len(URLs_list) == 0:  # if the URLs list empty generate new one
            word_net_id = WordNet_ID_list.pop()  # get new word_net_id
            createURLsList(word_net_id)  # generate new URLs list
            print("WordNet ID list has elements {} left ".format(len(WordNet_ID_list)))
        url = URLs_list.pop()  # get URL to download the image
        try:
            img_name = f"{valid_images}.jpg"  # create the image name
            urllib.request.urlretrieve(url, output_path + img_name)  # get the image and save it
            try:
                width, height = verifyImage(img_name, output_path)  # verify the image and get width & height for check
                if width < 200 or height < 200:  # if the height or the width less than 200 delete the image
                    deleteImage(img_name, output_path)
                    low_resolution_image += 1  # invalid image increased
                resizeImage(img_name, output_path)  # resize the image to (224,224)
                valid_images += 1  # valid image increased after verifying and resizing image
            except (IOError, SyntaxError):
                deleteImage(img_name, output_path)  # delete image if it's not valid
                invalid_images += 1  # invalid image increased
        except Exception:
            invalid_links += 1  # invalid links increased

        itercounter += 1
        if itercounter % 50 == 0:
            print('in iteration number : {} there is {} Valid images with size (224,224) saved, {} Invalid images '
                  'deleted,{} low resolution image deleted and {} Invalid '
                  'Links"'.format(itercounter, valid_images, invalid_images, low_resolution_image, invalid_links))


'''def main(num_downloaded_img, path):
    downloadSamples(num_downloaded_img, path)


if __name__ == '__main__':
    num_downloaded_img = 100  # number of samples to be downloaded
    output_path = '../../data/samples'  # output folder path
    getWNIDPage()  # to be executed only one time to initialize the lists needed to generate Links
    main(num_downloaded_img, output_path)  # to be executed as many as we want samples and there is
'''