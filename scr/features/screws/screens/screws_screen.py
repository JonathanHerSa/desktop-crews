import tkinter as tk

import numpy

from scr.config.styles import Styles
from scr.features.screws.partials.camara_frame import CamaraFrame
from scr.features.screws.partials.settings_frame import SettingsFrame

from scr.features.screws.partials.table_frame import TableFrame
from scr.utils.capture_camaras import CaptureCameras
from scr.features.repositories.keras_rnns_respository import KerasRnnsRepository


class ScrewsScreen(tk.Tk):
    
    neural_networks = KerasRnnsRepository()
    models =[]
    capture_frame = None
    capture_predictions = []
    
    def __init__(self):
        super().__init__()
        self.title("Conteo de Tornillos")
        self.bind('<Escape>', lambda e: self.quit())
        # Dimesiones Anchura x Altura
        screen_style = Styles.screen_style()
        self.geometry(screen_style["geometry"])
        self.minsize(*screen_style["minsize"])
        self.attributes(*screen_style["attributes"])
        self.configure(background=screen_style["background"])

        self.captura_cameras = CaptureCameras()
        
        #add sections in screen
        self.section_camara = CamaraFrame(self,self.captura_cameras)
        self.section_camara.pack(side="top",fill="both", expand=False, padx=120, pady=20)

        self.label_loading = tk.Label(self, text="Cargando...", **Styles.label_normal_style())
        self.label_loading.pack(fill="both", expand=True)
        
        self.section_settings = SettingsFrame(self,
                                              on_predict=self.section_camara.start_video,
                                              on_stop_predict=self.section_camara.stop_video,
                                              on_change_camara=self.on_change_camara,
                                              on_change_model=self.on_change_model,
                                              on_capture=self.capture_predict
                                              )
        self.section_settings.pack(side="left", fill="both",padx=10, expand=True)
        
        self.section_table_results = TableFrame(self, on_select=self.select_predictions)
        self.section_table_results.pack(side="right",fill="both",padx=10, expand=True)       

        self.after(100, self.start_services)
        self.wait_visibility()
        self.bind('<Configure>', self.window_resize)
         
    
    def start_services(self): 
        self.start_camaras_service()
        self.after(100, self.start_rn_service)
        

    def start_camaras_service(self):
        self.captura_cameras.start()
        camaras = self.captura_cameras.camaras
        self.section_settings.set_camaras_combobox([c  for c in camaras.keys()])
        
    def start_rn_service(self):
        self.models = self.neural_networks.get_models()
        
        
        self.section_settings.set_rn_models_combobox(
            [ model["name"] for model in self.models]
        )
        if len(self.models) > 0:
            self.start_service_model(self.models[0])


    def window_resize(self,event):
        self.section_camara.resize_image(height=int((self.winfo_height())/2))

    def on_change_camara(self, _, value):
        camaras = self.captura_cameras.camaras
        self.captura_cameras.set_camera(camara_index=camaras[value])
        
    def on_change_model(self, index, _):
        model  = self.models[index]
        self.section_settings.stop_predict()
        self.start_service_model(model)
        
        
    def start_service_model(self, model):
        self.label_loading.config(text="Cargando red neuronal...")
        self.after(50, lambda: self.load_model(model) )
        
        
    def load_model(self,model):
        model, categories = self.neural_networks.load_model(model)
        self.section_camara.model = model
        self.section_camara.categories= categories
        self.label_loading.config(text="100% COMPLENTADO")
        self.after(1000, lambda: self.label_loading.config(text="") )
    
    def capture_predict(self):
        with_image, frame = self.section_camara.stop_video()
        self.capture_frame = None # para ver si la red fue predeciada
        predictions = []
        if with_image:
            must_predict = with_image and self.section_camara.categories is not None
            if must_predict:
                self.capture_frame = frame
                predictions, image_predict = self.section_camara.predictions_frame(frame)
                frame = self.section_camara.draw_predictions(image_predict=image_predict,predictions=predictions )
                
            self.capture_predictions = predictions
            self.section_camara.update_image_label(frame)
            self.section_table_results.update_prediction(predictions=predictions)
            
            
    def select_predictions(self,_, predictions_selected):
        if len(predictions_selected) == 0:
            predictions_selected = self.capture_predictions
        
        image_predict = self.section_camara.yolov8.convert_image(self.capture_frame)
        image_predict = image_predict.numpy()
        frame = self.section_camara.draw_predictions(image_predict=image_predict,predictions=predictions_selected )
        self.section_camara.update_image_label(frame)
        

        



