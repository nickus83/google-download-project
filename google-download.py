from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import os
import os.path as osp
import time
import requests
import hashlib
import base64


def find_largest(images):
    if not len(images):
        return None

    max_size = 0
    idx = None
    for count, image in enumerate(images):
        size  = max(image.size['height'], image.size['width'])
        if size >= max_size:
            max_size = size
            idx = count
    try:
        url = images[idx].get_attribute('src')
    except Exception as e:
        print(e)
        import pdb; pdb.set_trace()

    return url

def search_google(searchurl, maxcount):
    urls = []

    print("Searching google with request:")
    print(searchurl)

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--no-wifi')
    try:
        browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        # browser = webdriver.Chrome(chromedriver_path, options=options)
    except Exception as e:
        print(f'No found chromedriver in this environment.')
        print(f'Install on your machine. exception: {e}')
        print('No chromedriver')
        return
    
    # browser.set_window_size(1280, 1024)
    browser.set_window_size(1920, 1080)
    browser.get(searchurl)
    time.sleep(1)
    
    body = browser.find_element_by_id('islrg')
    main_window = browser.window_handles[0]

    elements = body.find_elements_by_tag_name('a')
    
    for count, element in enumerate(elements):
        try:
            element.click()
        except Exception as e:
            print(f"{e} in searching")
            pass
        else:
            # url find here
            large_body = browser.find_element_by_id('islsp')
            images = large_body.find_elements_by_tag_name('img')
            url = find_largest(images)
        finally:
            # if more than one tab is open -> close it
            if len(browser.window_handles) > 1:
                browser.switch_to_window(browser.window_handles[1])
                browser.close()
                browser.switch_to_window(main_window)

            if url and url not in urls:
                urls.append(url)

            if len(urls) >= int(maxcount):
                break
        
    browser.quit()
    return urls

def parse_images(images):
    urls = []
    print("Parsing images urls.")
    
    for image in images[1:]:
        try:
            url = image['data-src']
            if not url.find('https://'):
                urls.append(url)
        except:
            try:
                url = image['src']
                if not url.find('https://'):
                    urls.append(image['src'])
            except Exception as e:
                print('No found image sources.')
                print(e)
    
    return urls

def prepare_dir(dirname):
    if not osp.exists(dirname):
        os.makedirs(dirname)

def download_urls(urls, searchwords, output_dir):

    prepare_dir(output_dir)
    output = osp.join(output_dir, str(searchwords))
    prepare_dir(output)

    assert urls
    
    repeat_count = 0
    for url in tqdm(urls):
        if 'base64' in url:
            try:
                rawdata = base64.b64decode(url.split(',')[-1])
            except Exception as e:
                print(f'Failed to write base64 data with {e}')
        else:
            try:
                res = requests.get(url, verify=False, stream=True)
                rawdata = res.raw.read()
            except Exception as e:
                print('Failed to write rawdata.')
                print(e)

        hashname = hashlib.md5(rawdata).hexdigest()
        image_name = hashname + '.jpg'
        image_path = osp.join(output, image_name)

        if not osp.exists(image_path):
            with open(image_path, 'wb') as f:
                f.write(rawdata)
        else:
            repeat_count += 1
        
    print(f"Found {repeat_count} repeated images.")
            
# Main block
def main(words, keywords_file, maxcount, output_dir):

    if not words and osp.exists(keywords_file):
        words = []
        with open(keywords_file, encoding='utf-8') as f:
            for line in f.readlines():
                words.append(line.rstrip())

    searchpart = '+'.join(words)
    searchurl = 'https://www.google.com/search?q=' + searchpart\
                + '&source=lnms'\
                + '&tbm=isch'\
                + '&num={}'.format(str(maxcount))
    
    urls = search_google(searchurl, maxcount)

    download_urls(urls, searchpart, output_dir)


if __name__ == '__main__':
    local_dir = osp.dirname(osp.abspath(__file__))

    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('-o', '--output-dir', default=osp.join(local_dir, 'pictures'),
                                    help="path to output local dir, default=local 'pictures'")
    p.add_argument('-m', '--maxcount', default=100, help='maximum count images, default=100')
    keywords = p.add_mutually_exclusive_group()
    keywords.add_argument('-w', '--words', nargs='+', help='searchwords list')
    keywords.add_argument('-f', '--keywords-file', type=osp.normpath,
                    default=osp.join(local_dir, 'keywords.txt'), help='searchwords list file')
    args = p.parse_args()
    
    main(**vars(args))