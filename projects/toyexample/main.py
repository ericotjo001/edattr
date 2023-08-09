import os, argparse
from setup import *
from toydata import prep_toyexample_dir, save_toyexample_csv

#######################################
#      Basic Data Preprocessing 
#######################################
# For classifier task

def prepare_data(**kwargs):
    print('=== prepare toy data ===')
    v = kwargs['verbose']

    # Let's create a raw toy data, if not yet created
    # By default, we put our data somewhere in "Desktop/edattr.ws/data"
    DATA_DIR = prep_toyexample_dir(**kwargs)
    if not os.path.exists(DATA_DIR): save_toyexample_csv(DATA_DIR)

    # We like to create the directory variable explicitly. Why not?
    from edattr.factory import manage_dirs
    DIRS = manage_dirs(**kwargs)

    # Load our raw toy data - see above (assume it's in the form of csv file)
    import pandas as pd
    df = pd.read_csv(DIRS['DATA_DIR'], index_col=False)

    # Do some pre-processing of your csv data here
    from edattr.data import dfPP
    dfpp = dfPP() # create the processor
    processed_ = dfpp.process_dataframe(df, DIRS['DATA_CACHE_DIR'], TARGET_LABEL_NAME, verbose=v)
    print('Data cache at', DIRS['DATA_CACHE_DIR'])

    # Do visualization here
    from edattr.data import DataVis
    datavis = DataVis(DIRS['DATA_VIS_DIR']) # create the visualization object
    datavis.vis(df, processed_['df_processed'], TARGET_LABEL_NAME=TARGET_LABEL_NAME, verbose=v)
    print('Data visualization at', DIRS['DATA_VIS_DIR'])

#######################################
#           Main Processes
#######################################

def toy_kfold_train_val_test_endorse(parser):
    # Note: with large epochs of training, it's pretty easy to obtain perfect accuracy
    # But for analyzing endorsement method, we will stop training early
    parser.add_argument('--toggle', default=None, type=str, help=None)  
    parser.add_argument('--n_epochs', default=64, type=int, help=None)  
    parser.add_argument('--batch_size', default=32, type=int, help=None)

    parser.add_argument('--DEV_ITER', default=0, type=int, help=None)

    args, unknown = parser.parse_known_args()
    kwargs = vars(args)  # is a dictionary    
    kwargs.update({'prefix':'k'})

    from edattr.factory import manage_dirs
    DIRS = manage_dirs(**kwargs)

    # imported from setup.py
    kf = kFold_Toy(DIRS, **kwargs) 

    from edattr.endorse import kFoldClassifierEndorsementVis
    kfev = kFoldClassifierEndorsementVis(DIRS,**kwargs)    

    TOGGLE = kwargs['toggle'] 
    if TOGGLE == '0':
        kf.log_model_number_of_params(**kwargs); exit()

    if TOGGLE is None: TOGGLE = '11111'
    if TOGGLE[0] == '1':
        kf.train_val_test(verbose=kwargs['verbose'])
        kf.visualize_output()
    if TOGGLE[1] == '1':
        kf.endorse_selected_models(**kwargs)
        kfev.visualize_endorsement_selected_models(**kwargs)  
    if TOGGLE[2] == '1':        
        kf.eec_partition_selected_models(**kwargs)   
        kf.eec_selected_models(**kwargs)   
    if TOGGLE[3] == '1':
        kf.post_eec_train_val_test(**kwargs)
        kf.visualize_post_eec_output(**kwargs)

    # Additional section: if you want to compare with common ML algorithms
    if TOGGLE[4] == '1':
        from edattr.cmlpackage import kFoldCommonMLClassifierPipeline
        cml = kFoldCommonMLClassifierPipeline(kf,TARGET_LABEL_DICTIONARY=None)
        cml.train_test_common_ml_classifiers()

        kf.kwargs['compare-common-ml'] = True
        kf.visualize_post_eec_output(**kwargs)

def toy_kfold_aggregate(parser):
    print('toy_kfold_aggregate...')
    args, unknown = parser.parse_known_args()
    kwargs = vars(args)  # is a dictionary  
    kwargs.update({'prefix':'k','label': 'dummylabel'})   

    label_suffix = 'toy_kfold'
    from edattr.aggregator import aggregate_val_test_results
    aggregate_val_test_results(label_suffix=label_suffix, **kwargs)

    from edattr.setup_template import DataSetupTypeK1, DatasetTypeK1
    from edattr.aggregator import aggregate_endorsement_samples, aggregate_endorsement_samples_vis
    kwargs.update({
        'TARGET_LABEL_NAME': TARGET_LABEL_NAME,
        'feature_mode': None,
        'endorsement_mode' : 'shap-lime-top2',
        })
    aggregate_endorsement_samples(DataSetupTypeK1, DatasetTypeK1, label_suffix=label_suffix, **kwargs)
    aggregate_endorsement_samples_vis(label_suffix=label_suffix, **kwargs)

    from edattr.factory import clean_up_directory
    clean_up_directory(**kwargs)  # let's do a bit of cleanup, delete folder with 'dummylabel'

WORKSPACE_DIR_INFO = """Default workspace is at ~/Desktop/edattr.ws"""
DATA_DIR_INFO = """Full directory, if specified. Otherwise, consider putting the csv file into <WORKSPACE_DIR>/data"""
DATA_PROCESSING_DIR_INFO = "Where to store the results of preprocessing your data."
LABEL_INFO = "Label determines the preset configuration (see setup.py)."

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=None)

    parser.add_argument('-m','--mode', default=None, type=str, help=None)
    parser.add_argument('-v','--verbose', default=100, type=int, help=None)
    parser.add_argument('-w','--WORKSPACE_DIR', default=None, type=str, help=WORKSPACE_DIR_INFO)

    parser.add_argument('--DATA_FILE_NAME', default='toyexample.csv', type=str, help=None)
    parser.add_argument('--DATA_DIR', default=None, type=str, help=DATA_DIR_INFO)
    parser.add_argument('--DATA_PROCESSING_DIR', default=None, type=str, help=DATA_PROCESSING_DIR_INFO)

    parser.add_argument('--full_projectname', default='toyclassifier', type=str, help=LABEL_INFO)
    parser.add_argument('--label', default=None, type=str, help=None)   

    args, unknown = parser.parse_known_args()
    kwargs = vars(args)  # is a dictionary

    if kwargs['mode'] == 'preprocess_normalize':
        prepare_data(**kwargs)
    elif kwargs['mode'] == 'kfold':
        toy_kfold_train_val_test_endorse(parser)
    elif kwargs['mode'] == 'kfold_aggregate':
        toy_kfold_aggregate(parser)
    else:
        raise NotImplementedError('invalid mode?')
