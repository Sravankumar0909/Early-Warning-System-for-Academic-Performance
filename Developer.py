import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import random
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
import joblib
warnings.filterwarnings("ignore")
import sys
import sqlite3

df = pd.DataFrame()
models = pd.DataFrame()
class CollectData:
    def open_file_dialog(self):
        global df
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title="Select a File for training the Model")
        if file_path:
            print(f"Selected file : {file_path}")
            df = pd.read_csv(file_path)
            df['External'] = 0
            #print(df.head())
            for i in range(len(df)):
                if df['Internal'][i] >=35 :
                    df.loc[i,'External'] = random.randint(50,60)
                elif df['Internal'][i] >= 30 and df['Internal'][i] <35:
                    df.loc[i,'External'] = random.randint(40,50)
                elif df['Internal'][i] >= 25 and df['Internal'][i] <30:
                    df.loc[i,'External'] = random.randint(30,40)
                elif df['Internal'][i] >=20 and df['Internal'][i]<25:
                    df.loc[i,'External'] = random.randint(20,30)
                elif df['Internal'][i] >=15 and df['Internal'][i]<20:
                    df.loc[i,'External'] = random.randint(15,25)
                else:
                    df.loc[i,'External'] = random.randint(0,15)
        else:
            print("File selection cancelled")
            sys.exit()
#cd = CollectData()
#cd.open_file_dialog()
#print(df.head(10))

class PreProcessing:
    def preprocess_data(self):
        global df
        for i in range(df.shape[1]):
            df[df.columns[i]] = pd.to_numeric(df.iloc[:,i],errors='coerce')
        df.fillna(0,inplace=True)
        #print(df.isin(['--']).sum())
        print(df.isna().sum())
        print(df.info())
    def analysis(self):
        for column in df:
            if column!='External':
                plt.figure(figsize=(8, 4))
                plt.scatter(df[column], df['External'], marker='o', color='blue')
                plt.xlabel(column)
                plt.ylabel('External')
                plt.title(f'Scatter Plot: {column} vs. External')
                plt.grid(True)
                plt.show()
#pda = PreProcessing()
#pda.preprocess_data()
#pda.analysis()

class Model:
    def __init__(self):
        self.X = df['Internal']
        self.y = df['External']
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X,self.y,test_size=0.2,random_state=42)
        self.X_train = self.X_train.values.reshape(-1,1)
        self.y_train = self.y_train.values.reshape(-1,1)
        self.X_test = self.X_test.values.reshape(-1,1)
        self.y_test = self.y_test.values.reshape(-1,1)
    def evaluation(self, y_test, prediction):
        mse = mean_squared_error(y_test, prediction)
        mae = mean_absolute_error(y_test, prediction)
        r_squared = r2_score(y_test, prediction)
        rmse = np.sqrt(mse)
        return mse, mae, r_squared, rmse
    def rmse_cv(self, model, X_train, y_train):
        scores = cross_val_score(model, X_train, y_train, cv = 5, scoring='neg_mean_squared_error')
        rmse_cross_val = np.sqrt(-scores)
        return rmse_cross_val
    def modelfit(self):
        global models
        #Linear
        lin_reg = LinearRegression()
        lin_reg.fit(self.X_train, self.y_train)
        prediction =lin_reg.predict(self.X_test)
        mse, mae, r_squared, rmse = self.evaluation(self.y_test,prediction)
        rmse_cross_val = self.rmse_cv(lin_reg,self.X_train,self.y_train)
        data = {"MODEL":"LinearRegression","MSE":mse,"MAE":mae,"R2_SCORE":r_squared,"RMSE":rmse,"RMSE (CROSS-VALIDATION)":np.mean(rmse_cross_val)}
        new_row = pd.DataFrame(data,index=[0])
        models=pd.concat([models,new_row],ignore_index=True)
        #Ridge
        ridge = Ridge()
        ridge.fit(self.X_train, self.y_train)
        prediction = ridge.predict(self.X_test)
        mse, mae, r_squared, rmse = self.evaluation(self.y_test,prediction)
        rmse_cross_val = self.rmse_cv(ridge,self.X_train,self.y_train)
        data = {"MODEL":"RidgeRegression","MSE":mse,"MAE":mae,"R2_SCORE":r_squared,"RMSE":rmse,"RMSE (CROSS-VALIDATION)":np.mean(rmse_cross_val)}
        new_row = pd.DataFrame(data,index=[0])
        models=pd.concat([models,new_row],ignore_index=True)
        #SVR
        svr = SVR(C=100000)
        svr.fit(self.X_train, self.y_train)
        prediction = svr.predict(self.X_test)
        mse, mae, r_squared, rmse = self.evaluation(self.y_test,prediction)
        rmse_cross_val = self.rmse_cv(svr,self.X_train,self.y_train)
        data = {"MODEL":"SVR","MSE":mse,"MAE":mae,"R2_SCORE":r_squared,"RMSE":rmse,"RMSE (CROSS-VALIDATION)":np.mean(rmse_cross_val)}
        new_row = pd.DataFrame(data,index=[0])
        models=pd.concat([models,new_row],ignore_index=True)
        #RandomForest
        random_forest = RandomForestRegressor()
        random_forest.fit(self.X_train, self.y_train)
        prediction = random_forest.predict(self.X_test)
        mse, mae, r_squared, rmse = self.evaluation(self.y_test,prediction)
        rmse_cross_val = self.rmse_cv(random_forest,self.X_train,self.y_train)
        data = {"MODEL":"RandomForestRegressor","MSE":mse,"MAE":mae,"R2_SCORE":r_squared,"RMSE":rmse,"RMSE (CROSS-VALIDATION)":np.mean(rmse_cross_val)}
        new_row = pd.DataFrame(data,index=[0])
        models=pd.concat([models,new_row],ignore_index=True)
        global prediction2
        prediction2 = random_forest
        print(models.sort_values(by='R2_SCORE'))
#m = Model()
#m.modelfit()

#print(models)
class SaveModel:
    def saving(self):
        model_filename = 'prediction2.joblib'
        joblib.dump(prediction2, model_filename)
        import sqlite3
        db_file_path = 'ews.db'
        conn = sqlite3.connect(db_file_path)

        try:
            cursor = conn.cursor()
            with open(model_filename, 'rb') as model_file:
                model_binary = model_file.read()
            sql = "INSERT INTO model (model_name, model_blob) VALUES (?, ?)"

            cursor.execute(sql, ('Random Forest', model_binary))

            conn.commit()

        finally:

            cursor.close()
            conn.close()




class EarlyWarningSystem:
    def __init__(self):
        cd = CollectData()
        cd.open_file_dialog()
        pda = PreProcessing()
        pda.preprocess_data()
        pda.analysis()
        m = Model()
        m.modelfit()
        s = SaveModel()
        s.saving()
e = EarlyWarningSystem()