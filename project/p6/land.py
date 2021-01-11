# project: p6
# submitter: zdai38
# partner: none

import zipfile
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import io
import numpy as np


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

def open(name):
    c = Connection(name)
    return c

class Connection:
    def __init__(self, name):
        self.db = sqlite3.connect(name+".db")
        self.zf = zipfile.ZipFile(name+".zip")
        self.df = pd.read_sql("""
        SELECT * FROM 
        images INNER JOIN places 
        ON images.place_id = places.place_id""",self.db)
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()
    
    def list_images(self):
        return sorted(self.zf.namelist())

    def image_year(self, file_name):
        return int(self.df.loc[self.df["image"] == file_name]["year"].values[0])
    
    def image_name(self, file_name):
        return self.df.loc[self.df["image"] == file_name]["name"].values[0]
    
    def image_load(self, file_name):
        with self.zf.open(file_name) as f:
            buf = io.BytesIO(f.read())
            img = np.load(buf)
        f.close()
        return img
    
    def plot_img(self, file_name, ax):
        img = self.image_load(file_name)
        
        use_cmap = np.zeros(shape=(256,4))
        use_cmap[:,-1] = 1
        uses = np.array([
            [0, 0.00000000000, 0.00000000000, 0.00000000000],
            [11, 0.27843137255, 0.41960784314, 0.62745098039],
            [12, 0.81960784314, 0.86666666667, 0.97647058824],
            [21, 0.86666666667, 0.78823529412, 0.78823529412],
            [22, 0.84705882353, 0.57647058824, 0.50980392157],
            [23, 0.92941176471, 0.00000000000, 0.00000000000],
            [24, 0.66666666667, 0.00000000000, 0.00000000000],
            [31, 0.69803921569, 0.67843137255, 0.63921568628],
            [41, 0.40784313726, 0.66666666667, 0.38823529412],
            [42, 0.10980392157, 0.38823529412, 0.18823529412],
            [43, 0.70980392157, 0.78823529412, 0.55686274510],
            [51, 0.64705882353, 0.54901960784, 0.18823529412],
            [52, 0.80000000000, 0.72941176471, 0.48627450980],
            [71, 0.88627450980, 0.88627450980, 0.75686274510],
            [72, 0.78823529412, 0.78823529412, 0.46666666667],
            [73, 0.60000000000, 0.75686274510, 0.27843137255],
            [74, 0.46666666667, 0.67843137255, 0.57647058824],
            [81, 0.85882352941, 0.84705882353, 0.23921568628],
            [82, 0.66666666667, 0.43921568628, 0.15686274510],
            [90, 0.72941176471, 0.84705882353, 0.91764705882],
            [95, 0.43921568628, 0.63921568628, 0.72941176471],
        ])
        for row in uses:
            use_cmap[int(row[0]),:-1] = row[1:]
        use_cmap = ListedColormap(use_cmap)
        ax.set_title(str(self.image_year(file_name))+" "+ self.image_name(file_name))
        plt.imshow(img, cmap=use_cmap, vmin=0, vmax=255)
        return ax

    def lat_regression(self, use_code, ax):
        samp = self.df.loc[self.df["name"].str.startswith("samp")]
        
        lst = []
        for i in samp["image"]:
            code = self.image_load(i)
            perc = np.isin(code, use_code).mean()*100
            lst.append(perc)   
        target = np.array(lst).reshape(-1,1)
        
        lr = LinearRegression()
        lr.fit(samp[["lat"]].values, target)
        slope = lr.coef_[0][0]
        intercept = lr.intercept_[0]
        
        if ax != None:
            ax.scatter(samp[["lat"]].values, target)
            x0 = samp[["lat"]].values.min()-0.3
            x1 = samp[["lat"]].values.max()+0.3
            y0 = slope * x0 + intercept
            y1 = slope * x1 + intercept
            ax.plot((x0, x1),(y0,y1))
            plt.show()
    
        return (slope, intercept)
    
    def city_regression(self, list_code, year):
        cities = ["madison", "milwaukee", "greenbay", "kenosha", "racine", "appleton", "waukesha", "oshkosh", "eauclaire", "janesville"]
        
        city_list = {}
        for i in cities:
            df = self.df.loc[self.df["name"] == i]
#             print(i)
#             print(df)
            city_total = 0
            for j in list_code:
#                 print(j)
                lst = []
                for k in df["image"]:
                    code = self.image_load(k)
                    perc = np.isin(code, j).mean()*100
                    lst.append(perc)
                target = np.array(lst).reshape(-1,1)
#                 print(target)
                
                lr = LinearRegression()
                lr.fit(df[["year"]].values, target)
                pred_val = lr.predict(np.array([year]).reshape(-1,1))
#                 print(pred_val[0][0])
                city_total += pred_val[0][0]
            city_list[i] = city_total
        city = max(city_list, key=city_list.get)
        city_pred = city_list[city]
        return (city, city_pred)
    
    def city_plot(self, name ):
        use_codes = {11:'Open Water', 12: 'Perennial Ice/Snow', 
                     21: "Developed, Open Space", 22: "Developed, Low Intensity",
                     23: "Developed, Medium Intensity", 24: "Developed, High Intensity",
                     31: "Barren Land (Rock/Sand/Clay)", 41: "Deciduous Forest",
                     42: "Evergreen Forest", 43: "Mixed Forest",
                     51: "Dwarf Scrub (Alaska)", 52: "Shrub/Scrub",
                     71: "Grassland/Herbaceous", 72: "Sedge/Herbaceous (Alaska)",
                     73: "Lichens (Alaska)", 74: "Moss (Alaska)",
                     81: "Pasture/Hay", 82: "Cultivated Crops",
                     90: "Woody Wetlands", 95: "Emergent Herbaceous Wetlands"}
        
        df = self.df.loc[self.df["name"] == name]
        data = pd.DataFrame()
        data["year"] = df["year"]
        for i in use_codes:
            lst = []
            for j in df["image"]:
                code = self.image_load(j)
                perc = np.isin(code, i).mean()*100
                lst.append(perc)
            if not all(v == 0 for v in lst):
                data[i] = lst
        data = data.set_index("year")
                    
        fig, ax = plt.subplots()
        ax.set_xlabel("Year")
        ax.set_ylabel("Percent")
        ax.set_title(name)
        
        for i in data:
            ax.plot(data[i], label = i)

#         ax.plot(data)
        plt.legend(use_codes.values(),bbox_to_anchor=(1, 1), fontsize='xx-small')        
        plt.show()
        return ax
        

    def close(self):
        self.db.close()
        self.zf.close()
    

    
    
    
    