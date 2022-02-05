
import os
import numpy as np
import pandas as pd
import seaborn as sn
import matplotlib.pyplot as plt
import nrrd
import scipy.stats as ss
import SimpleITK as stik
import glob
from PIL import Image
from collections import Counter
import skimage.transform as st
from datetime import datetime
from time import gmtime, strftime
import pickle
import tensorflow
from tensorflow.keras.models import Model
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix



def model_pred(body_part, df_img, img_arr, out_dir, thr_img=0.5, thr_pat=0.5):    

    """
    model prediction for IV contrast

    Arguments:
        df_img {pd.df} -- dataframe with scan and axial slice ID.
        img_arr {np.array} -- numpy array stacked with axial image slices.
        model_dir {str} -- directory for saved model.
        saved_model {str} -- saved model name.
        pred_dir {str} -- directory for results output.

    Keyword arguments:
        thr_img {float} -- threshold to determine prediction class on image level.
        thr_pat {float} -- threshold to determine prediction class on patient level. 

    return:
        dataframes of model predictions on image level and patient level
    """
    
    model_dir = os.path.join(out_dir, 'model')
    pred_dir = os.path.join(out_dir, 'pred')
    os.mkdir(model_dir) if not os.path.isdir(model_dir) else None
    os.mkdir(pred_dir) if not os.path.isdir(pred_dir) else None

    if body_part == 'head_and_neck':
        saved_model = 'EffNet_2021_08_24_09_57_13'
    elif body_part == 'chest':
        saved_model = 'Tuned_EfficientNetB4_2021_08_27_20_26_55'

    ## load saved model
    print(saved_model)
    model = load_model(os.path.join(model_dir, saved_model))
    ## prediction
    y_pred = model.predict(img_arr, batch_size=32)
    y_pred_class = [1 * (x[0] >= thr_img) for x in y_pred]
    #print(y_pred)
    #print(y_pred_class)

    ## save a dataframe for prediction on image level
    df_img['y_pred'] = np.around(y_pred, 3)
    df_img['y_pred_class'] = y_pred_class
    df_img_pred = df_img[['pat_id', 'img_id', 'y_pred', 'y_pred_class']] 
    fn = 'df_img_pred' + '_' + str(saved_model) + '.csv'
    df_img_pred.to_csv(os.path.join(out_dir, fn), index=False) 
    
    ## calcualte patient level prediction
    df_img_pred.drop(['img_id'], axis=1, inplace=True)
    df_mean = df_img_pred.groupby(['pat_id']).mean()
    preds = df_mean['y_pred']
    y_pred = []
    for pred in preds:
        if pred > thr_pat:
            pred = 1
        else:
            pred = 0
        y_pred.append(pred)
    df_mean['predictions'] = y_pred
    df_mean.drop(['y_pred', 'y_pred_class'], axis=1, inplace=True)
    df_pat_pred = df_mean 
    fn = 'df_pat_pred' + '_' + str(saved_model) + '.csv'
    df_pat_pred.to_csv(os.path.join(out_dir, fn))
    print('image level pred:\n', df_img_pred)
    print('patient level pred:\n', df_pat_pred)


    

    