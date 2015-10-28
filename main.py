from time import sleep

__author__ = 'tal'

from bs4 import BeautifulSoup
import urllib2
from urlparse import urljoin
from Queue import Queue
# Display()
from pyvirtualdisplay import Display
# helping functions
from helper import *
# generate keys for data_dict (same element that appears on two different pages must appear only once on data_dict)
import hashlib
# print data_dict like a boss (yeah right)
import pprint
# split work on many threads. serial computation is not necessary
import threading
# measure execution time
import time


#flag for full/partial screenshot of webpage
screenshot_fullscreen_flag = False
# flag for capturing all urls screenshots. if True then adding urls to capture_url_queue is not over. if False just take urls from capture_url_queue until empty.
threads_working = None
# eliminate recursion
not_visited_queue = Queue()
# queue of urls to screenshot
capture_url_queue = Queue()
# visited urls. do not re-visit to avoid circular
marked_urls = []

# data center
'''
    'forms'  :   [
                 hash(form_1) : [data, [url1,url2,...]]
                 hash(form_2) : [data, [url1,url2,...]]
                 ...
                ]

'''

# where we store all the information
data_dict = dict()

# program prog_input
prog_input = None

# key in data_dict where all domain urls of checked website are sotred
DICT_ALL_PAGES = 'ALL_PAGES_IN_DOMAIN'


def parse_url(url):
    print ('visiting: ' + url)

    # connect & read page
    try:
        hdr = {'User-Agent': 'Mozilla/5.0'}
        # without hdr I get 403 Forbidden error
        req = urllib2.Request(url, headers=hdr)
        page = urllib2.urlopen(req)
        if not 'text/html' in page.headers['Content-Type']:
            # do not process non-web content (files etc...)
            return
        soup = BeautifulSoup(page.read())
    except Exception, e:
        print e
        return

    # get all next pages to visit
    for tag in soup.findAll('a', href=True):
        next_url = urljoin(url, tag['href'])
        # check if next_url is valid
        if 'javascript:' in next_url or \
                next_url.__contains__('@') or \
                not same_domain(next_url, url):
            continue

        if next_url not in marked_urls:
            marked_urls.append(next_url)  # add url to visited-list
            not_visited_queue.put(next_url)

    # add url to screenshot list
    capture_url_queue.put((url,None))

    # get desired info from page
    for user_entry_name in prog_input:  # user_entry = youtube, downloadable, ...
        elements = find_elements(soup, prog_input[user_entry_name])  # find all elements according to specified input
        if elements == []:  # if no elements found on html, skip to
            continue  # next user -added category
        for e in elements:  # add each element to the dictionary and
            h = hashlib.md5(str(e))  # add all URLs contatining it
            key = h.hexdigest()
            if not data_dict[user_entry_name].has_key(key):
                # check if user wants to take image. default action is to take image
                if prog_input[user_entry_name].has_key('take_image') and not prog_input[user_entry_name]['take_image']:
                    img_path = '**' + user_entry_name
                else:
                    img_path = capture_image_of_element(url, e)  # take image of element
                data_dict[user_entry_name][key] = [e, img_path, []]  # add new element to dictionary
            data_dict[user_entry_name][key][2].append(url)  # add url to element known-url-list
    return


def take_imgae(tup):
    url = tup[0]
    element = tup[1]
    img_path = capture_image_of_element(url, element) # element == None ==> take screenshot of full webpage
    tup = (url, img_path)
    data_dict[DICT_ALL_PAGES].append(tup)


def screenshot_urls_from_queue():
    while not capture_url_queue.empty():
        tup = capture_url_queue.get()
        take_imgae(tup)


def init_data_from_input(input):
    global data_dict

    for key in input.keys():
        data_dict[key] = dict()  # {'youtube': {}, 'downloadable': {}}

    # data in entry: [url , pic_of_url]
    data_dict[DICT_ALL_PAGES] = []

    print data_dict


def prase_urls(thr_num):
    while not not_visited_queue.empty():
        # print 'active threads: ' + str(threading.activeCount())
        print 'thread-' + str(thr_num) + ' is working'
        url = not_visited_queue.get()
        parse_url(url)
    print 'thread-' + str(thr_num) + ' EMPTY QUEUE'


def create_threads_and_start_working(first_url, thread_num, sleep_time):
    # init stuff
    not_visited_queue.put(first_url)
    marked_urls.append(first_url)

    # event = threading.Event()  #http://bioportal.weizmann.ac.il/course/python/PyMOTW/PyMOTW/docs/threading/index.html

    threads = []
    i = 0
    while len(threads) < thread_num:
        t = threading.Thread(target=prase_urls, args={i, })
        threads.append(t)
        i += 1

    # start first thread
    threads[0].start()

    # wait for it to get urls so other threads won't see queue as empty and die
    sleep(sleep_time)

    # start other threads
    for i in range(1, thread_num):
        threads[i].start()
    # wait for all threads to finish

    for i in range(0, thread_num):
        threads[i].join()

    # start capturing full-screen URLs
    cap_url_thr_num = 23
    cap_url_threads = []
    i = 0
    while len(cap_url_threads) < cap_url_thr_num:
        t = threading.Thread(target=screenshot_urls_from_queue)
        cap_url_threads.append(t)
        i += 1

    # start other threads
    print 'started capture threads'
    for i in range(0, cap_url_thr_num):
        cap_url_threads[i].start()
    # wait for all threads to finish

    for i in range(0, cap_url_thr_num):
        cap_url_threads[i].join()

    print 'all threads finished'

    return


def main():
    global prog_input

    start_time = time.time()

    # set first url

    url = "http://www.reactful.com"

    prog_input = {
        'forms': {
            'element': 'form',
        },
        'downloadable': {
            'attributes': [
                ('href', '(.+)\.pdf$')
            ],
            'element': 'a',
            'take_image': False
        }
    }
    # {, 'youtube': {'attributes': [('src', '*youtube*')], 'element': 'iframe'},

    # disable the need to open a web browser physically when screenshotting
    display = Display(visible=0, size=(800, 600))
    display.start()

    # initialize data dictionaries
    init_data_from_input(prog_input)

    # start
    create_threads_and_start_working(first_url=url, thread_num=8, sleep_time=7)

    # print result dictionary
    pprint.pprint(data_dict)

    end_time = time.time()
    total_time = end_time - start_time
    print 'total execution time:' + str(total_time)

if __name__ == "__main__": main()

'''
TO DO:

1.
 added 'take_image' flag by user to know wether to take a picture of the element.
 if take_image=False, set img_path to '**SOME_NAME**' for later reference

STATUS: Done

2.
 add option to take screenshot of full webpage / just first view (As seen on browser)

STATUS: DONE.
        ADDED global flag 'screenshot_fullscreen_flag' which helper.py reads when taking a screenshot.
'''
