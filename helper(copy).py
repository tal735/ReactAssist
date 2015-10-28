__author__ = 'tal'

# url examination
import tldextract
import itertools
# element image capturing
from selenium import webdriver
from PIL import Image
import re

# this method gets an element with its element type and extracts the required data from it
def find_elements(soup, user_input):
    tag = user_input['element']
    attrs_dict = dict()

    if user_input.has_key('attributes'):
        user_attrs = user_input['attributes']
        for attr_tuple in user_attrs:
            attr_key = attr_tuple[0]
            attr_val = attr_tuple[1]
            attrs_dict[attr_key] = re.compile(attr_val)

    elements = soup.find_all(name=tag, attrs=attrs_dict)

    return elements

    '''
     thumb_url = 'http://img.youtube.com/vi/{vid_id}/0.jpg'.format(  #large = 0.jpg , small = 2.jpg https://djangosnippets.org/snippets/2234/
                    vid_id=src[src.rfind('/') + 1:].split('?')[0])

                        def find_all(self, name=None, attrs={}, recursive=True, text=None,
                 limit=None, **kwargs):

    http://stackoverflow.com/questions/14257717/python-beautifulsoup-wildcard-attribute-id-search :
    dates = soup.findAll("div", {"id" : re.compile('date.*')})

    '''


# return true if next_url has the same domain as url, false otherwise
def same_domain(next_url, url):
    return tldextract.extract(next_url).registered_domain == tldextract.extract(url).registered_domain


def same_url(next_url, url):
    if next_url + '/' == url:
        return True
    if next_url == url + '/':
        return True
    return False


'''
TAKE  SCREENSHOT  OF  ELEMENT IN  WEB  PAGE
'''


def capture_image_of_element(url, e):
    print 'capture url: ' + url
    fox = webdriver.Firefox()
    fox.get(url)
    capture_image_of_element.counter += 1
    filename = 'screenshot' + str(capture_image_of_element.counter) + '.png'
    # now that we have the preliminary stuff out of the way time to get that image :D
    fox.save_screenshot(filename)  # saves screenshot of entire page
    # full screen capture. no specific element
    if e is not None:
        # find xpath of element e
        xpath = xpath_soup(e)

        print 'taking screenshot of specific element: ' + xpath
        element = fox.find_element_by_xpath(xpath)  # find part of the page you want image of
        location = element.location
        size = element.size
        im = Image.open(filename)  # uses PIL library to open image in memory
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']

        im = im.crop((left, top, right, bottom))  # defines crop points
        try:
            print 'Trying to save image ' + filename
            im.save(filename)  # saves new cropped image
            print('SUCCESS!')
        except Exception, e:
            print e

    fox.quit()
    return filename


# static variable of function. counts number of images
capture_image_of_element.counter = 0


def xpath_soup(element):
    """
    Generate xpath of soup element
    :param element: bs4 text or node
    :return: xpath as string
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        """
        @type parent: bs4.element.Tag
        """
        previous = itertools.islice(parent.children, 0, parent.contents.index(child))
        xpath_tag = child.name
        xpath_index = sum(1 for i in previous if i.name == xpath_tag) + 1
        components.append(xpath_tag if xpath_index == 1 else '%s[%d]' % (xpath_tag, xpath_index))
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)
