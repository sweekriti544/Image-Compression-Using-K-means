from tkinter import *
from tkinter import ttk, filedialog, messagebox, PhotoImage, Label
import base64
import os
from bs4 import BeautifulSoup
import requests
from urllib.request import urlopen
import os
import numpy as np
from skimage import io
from sklearn.cluster import MiniBatchKMeans
from matplotlib import pyplot as plt
import matplotlib.pyplot as mpimg
import cv2

config = {}


def fetch_url():
    url = _url.get()
    config['images'] = []
    _images.set(())

    try:
        page = requests.get(url)
    except requests.RequestException as rex:
        _sb(str(rex))
    else:
        soup = BeautifulSoup(page.content, 'html.parser')
        images = fetch_images(soup, url)
        if images:
            _images.set(tuple(img['name'] for img in images))
            _sb('Images found: {}'.format(len(images)))
        else:
            _sb('No images found!.')
        config['images'] = images


def fetch_images(soup, base_url):
    images = []
    for img in soup.findAll('img'):
       src = img.get('src')
       img_url = ('{base_url}/{src}'.format(base_url=base_url, src=src))
       name = img_url.split('/')[-1]
       if name[-3:] == "png" or name[-3:] == "jpg": ### <- here
           images.append(dict(name=name, url=img_url))
    return images


def fetch_selected_images(event):
    widget = event.widget
    selected_idx = widget.curselection()
    selected_items = [widget.get(int(item)) for item in selected_idx]
    selected_images = []
    url = _url.get() + '/img'

    for img in selected_items:
        img_url = ('{base_url}/{src}'.format(base_url=url, src=img))
        name = img_url.split('/')[-1]
        if name in selected_items:
            selected_images.append(dict(name=name, url=img_url))
        for idx in selected_idx:
            widget.itemconfig(idx, fg='red')

    config['images'] = selected_images


def save():
    if not config.get('images'):
        _alert('No images to save!')
        return

    if _save_method.get() == 'img':
        dirname = filedialog.os.getcwd()
        _save_images(dirname)


def _save_images(dirname):
    i = 1
    if dirname and config.get('images'):
        for img in config['images']:
            img_data = requests.get(img['url']).content
            filename = str(i)
            i = i + 1
            with open(filename + '.png', 'wb') as f:
                f.write(img_data)
        _alert('Done')


def compress():
    algorithm = "full"
    for f in os.listdir('.'):
        if f.endswith('.png'):
            image = io.imread(f, 0)
            rows = image.shape[0]
            cols = image.shape[1]

            pixels = image.reshape(image.shape[0] * image.shape[1], image.shape[2])
            kmeans = MiniBatchKMeans(n_clusters=128, n_init=10, max_iter=200)
            kmeans.fit(pixels)

            clusters = np.asarray(kmeans.cluster_centers_, dtype=np.uint8)
            labels = np.asarray(kmeans.labels_, dtype=np.uint8)
            labels = labels.reshape(rows, cols)
            colored = clusters[labels]

            #  np.save('codebook'+f+'.npy', clusters)
            io.imsave('compressed_' + f, colored)

            img1 = mpimg.imread(f, 0)
            img2 = mpimg.imread('compressed_' + f, 0)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 10))
            ax1.imshow(img1)
            ax1.set_title('Original image')
            org = int(os.stat(f).st_size / 1024)
            ax1.set_xlabel('The size is %d' % org +'kB')
            ax2.imshow(img2)
            ax2.set_title('Compressed image')
            comp = int(os.stat('compressed_' + f).st_size / 1024)
            ax2.set_xlabel('The size is %d' % comp +'kB')
            plt.show()

            fig, ax = plt.subplots(2, 1)

            img = cv2.imread(f, 0)
            ax[0].hist(img.ravel(), 256, [0, 256]);
            ax[0].set_title("Original image")
            plt.xlabel('Intensity', fontsize=13)
            plt.ylabel('No. of pixels', fontsize=13)
            img1 = cv2.imread('compressed_' + f, 0)
            ax[1].hist(img1.ravel(), 256, [0, 256]);
            ax[1].set_title("Compressed image")
            plt.xlabel('Intensity', fontsize=13)
            plt.ylabel('No. of pixels', fontsize=13)
            plt.show()
            print('size of original image: ', int(os.stat(f).st_size / 1024), 'kB')
            print('size of compressed image:', int(os.stat('compressed_' + f).st_size / 1024), 'kB')

    _alert('Done')


def _sb(msg):
    _status_msg.set(msg)


def _alert(msg):
    messagebox.showinfo(message=msg)


if __name__ == "__main__":
    _root = Tk()
    style = ttk.Style()
    style.configure("TButton", foreground="black", background="seashell3")
    _root.title('Image Compression using K-means Clustering')

    imgicon = PhotoImage(file=os.path.join(r'giphy.gif'))
    _root.tk.call('wm', 'iconphoto', _root._w, imgicon)

    _root.resizable(width=FALSE, height=FALSE)

    _mainframe = ttk.Frame(_root, padding='5 5 5 5')
    _mainframe.grid(row=0, column=0, sticky=(E, W, N, S))

    _url_frame = ttk.LabelFrame(_mainframe, text='URL', padding='5 5 5 5')
    _url_frame.grid(row=0, column=0, sticky=(E, W),columnspan=2)
    _url_frame.columnconfigure(0, weight=1)
    _url_frame.rowconfigure(0, weight=1)

    _url = StringVar()
    _url.set('http://')
    _url_entry = ttk.Entry(_url_frame, width=100, textvariable=_url)
    _url_entry.grid(row=0, column=0, sticky=(E, W, S, N), padx=5)
    _fetch_btn = ttk.Button(_url_frame, text='Fetch info from URL', command=fetch_url)

    _fetch_btn.grid(row=0, column=1, sticky=W, padx=5)

    _img_frame = ttk.LabelFrame(
        _mainframe, text='Content', padding='9 0 0 0'
    )
    _img_frame.grid(row=1, column=0, sticky=(N, S, E, W),columnspan=2)
    _images = StringVar()
    _img_listbox = Listbox(
        _img_frame, listvariable=_images, height=6, width=100, selectmode='multiple'
    )
    _img_listbox.grid(row=0, column=0, sticky=(E, W), pady=5)
    _img_listbox.bind('<<ListboxSelect>>', fetch_selected_images)

    _scrollbar = ttk.Scrollbar(
        _img_frame, orient=VERTICAL, command=_img_listbox.yview
    )
    _scrollbar.grid(row=0, column=1, sticky=(S, N), pady=6)
    _img_listbox.configure(yscrollcommand=_scrollbar.set)

    _radio_frame = ttk.Frame(_img_frame)
    _radio_frame.grid(row=0, column=2, sticky=(N, S, W, E))

    _choice_lbl = ttk.Label(_radio_frame, text='')
    _choice_lbl.grid(row=0, column=0, padx=5, pady=5)
    _save_method = StringVar()
    _save_method.set('img')

    _img_only_radio = ttk.Radiobutton(
        _radio_frame, text='As Images', variable=_save_method, value='img'
    )
    _img_only_radio.grid(row=1, column=0, padx=5, pady=2, sticky=W)
    _img_only_radio.configure(state='normal')

    _scrape_btn = ttk.Button(
        _mainframe, text='Scrape!', command=save,style='TButton'
    )
    _scrape_btn.grid(row=2, column=0, sticky=(N,E), pady=2)

    _compress_btn = ttk.Button(
        _mainframe, text='Compress!', command=compress
    )
    _compress_btn.grid(row=2, column=1, sticky=W, pady=2)

    _status_frame = ttk.Frame(
        _root, relief='sunken', padding='2 2 2 2'
    )
    _status_frame.grid(row=1, column=0, sticky=(E, W, S))
    _status_msg = StringVar()
    _status_msg.set('Type a URL to start scraping...')
    _status = ttk.Label(
        _status_frame, textvariable=_status_msg, anchor=W
    )
    _status.grid(row=0, column=0, sticky=(E, W))

    # context menu

    _menubar = Menu(_root)
    filemenu = Menu(_menubar, tearoff=0)
    filemenu.add_command(label='Fetch images from URL', command=fetch_url)
    filemenu.add_command(label='Scrape images', command=save)
    filemenu.add_command(label="Compress image", command=compress)
    filemenu.add_separator()


    def reset():
        _url.set('http://')
        _img_listbox.delete(0, 'end')
        _save_method.set('img')
        _status_msg.set('Type a URL to start scraping...')


    def about():
        ab_wnd = Toplevel()
        ab_wnd.title('About')
        string = 'Simple Image Compression app using K-means Clustering Algorithm. \n This app can be used to crawl ' \
                 'the images from any website and the downloaded images can be compressed in a bulk. '
        ab_lbl = Label(ab_wnd, text=string, justify=CENTER, anchor=W)
        ab_lbl.pack()
        ab_wnd.mainloop()


    def help():
        hp_wnd = Toplevel()
        hp_wnd.title('Help')
        text = 'App Info:\n'
        hp_head = Label(hp_wnd, text=text, justify=CENTER, font=('Courier', 15))
        hp_head.pack()
        text = ' - Fetch info from URL: Downloads all images from the selected URL and places their filenames in the listbox.\n - Scrape: Saves the selected images in a directory \n - Compress: Compress the batch of images using K-means Clustering Algorithm.'
        hp_text = Label(hp_wnd, text=text, justify=LEFT, font=('Times New Roman', 12))
        hp_text.pack()
        hp_wnd.mainloop()


    filemenu.add_command(label='Reset content', command=reset)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=_root.quit)
    _menubar.add_cascade(label="File", menu=filemenu)
    _menubar.add_command(label='Help', command=help)
    _menubar.add_command(label='About the app', command=about)

    _root.config(menu=_menubar)

    _root.mainloop()
