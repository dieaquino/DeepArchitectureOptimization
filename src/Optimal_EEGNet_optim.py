# -*- coding: utf-8 -*-
import keras
import tensorflow as tf
import tensorflow.keras.backend as K
import sys
import numpy as np
import gc
import math


from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import train_test_split
from tensorflow.keras import regularizers
from tensorflow.keras.constraints import max_norm
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.layers import Flatten
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Input, Conv2D, DepthwiseConv2D, SeparableConv2D, Activation, AveragePooling2D
from tensorflow.keras.models import Model


class EEGNetOptim():
    def __init__(self):
        # Classifier     
        self.layers = None
        self.generator = None
        self.discriminator = None
        self.combined = None
        self.batch_size = 20
        self.num_classes = 3
        self.epochs = 20
        # Internals
        self._created = False
        self._trained = False

    def script_layer(self, var_types, icount_type, ibeg_param, iend_param, cursor, array, idmodelo, prev_channels,
                     idmodelodetalle, idmodelodetallecapa, idcapa):

        bh = [var_types[i] for i in range(0, icount_type)]

        p_SQL = " SELECT * " \
                " FROM public.selecciona_parametro_type(%s, %s, %s) "
        cursor.execute(p_SQL, (idmodelo, idmodelodetalle, idcapa,))
        layers_records = cursor.fetchall()

        ch = []
        for row_ly in layers_records:
            ch.append(bh[row_ly[0]])

        p_SQL = " SELECT * " \
                " FROM public.datos_modelo_TYPE(%s) " \
                " WHERE idmodelodetalle = %s AND idmodelodetallecapa = %s AND idcapa = %s "
        cursor.execute(p_SQL, (idmodelo, idmodelodetalle, idmodelodetallecapa, idcapa,))
        layer_records = cursor.fetchall()

        iflag_layer = 0
        icount_layers = 0
        icount_param = 0
        clayer_name = ''
        clayer_def = ''
        iconcate = 0
        iorder_param = 0

        for row in layer_records:

            icount_layers += 1

            idorden = row[0]
            descapa = row[3]
            desparametro = row[4]
            idtipodato = row[7]
            valor = row[9]
            idmodelocapaparametro = row[10]
            idparametro = row[11]
            idpadre = row[15]
            espadre = row[16]
            base = row[17]
            idpadreorden = row[19]
            dimension = row[20]
            idcapa = row[21]

            if clayer_name != descapa and icount_layers > 1:
                clayer_def = clayer_def[:-1] + ')'
                # print(clayer_def)
                iflag_layer = 0
            if iflag_layer == 0:
                iflag_layer = 1
                clayer_name = descapa
                clayer_def = descapa + '('

            sparameter = valor
            if valor == '':  # VERIFICA SI LA CAPA EN CUESTION SE DEBE EVALUAR O NO
                sparameter = str(ch[icount_param])
                # si no es padre y si no es hijo
                if idpadre == 0 and espadre == 0:
                    p_SQL = " SELECT * " \
                            " FROM public.parametrosdetalle " \
                            " WHERE numero = %s and idparametro = %s"
                    cursor.execute(p_SQL, (ch[icount_param], idparametro,))
                    parameter_records = cursor.fetchall()
                    for parameter_row in parameter_records:
                        if idtipodato == 5:
                            if parameter_row[4] == 0:
                                sparameter = "'" + parameter_row[3] + "'"
                            else:
                                sparameter = parameter_row[3]
                    iconcate = 0
                else:
                    # si es un parametro padre
                    if espadre > 0:

                        if sparameter != '0':
                            # Si va a estar activo el parametro padre, empieza a concatenar
                            clayer_def = clayer_def + ' ' + desparametro + '='
                        else:
                            iorder_param = idorden
                    else:
                        # Si es hijo y tiene opciones
                        if idpadreorden != iorder_param:
                            if idtipodato == 5:
                                max_idparametro = 0
                                # EN ESTA CONSULTA HASTA QUE SUBPARAMETRO SE IRA
                                p_SQL = " SELECT MAX(idparametro) AS idparametro " \
                                        " FROM public.datos_modelo_type(%s) " \
                                        " WHERE idpadre = %s  AND idcapa = %s "
                                cursor.execute(p_SQL, (idmodelo, idpadre, idcapa,))
                                parameter_records = cursor.fetchall()
                                for parameter_row in parameter_records:
                                    max_idparametro = parameter_row[0]

                                p_SQL = " SELECT * " \
                                        " FROM public.parametrosdetalle " \
                                        " WHERE numero = %s AND idparametro = %s"
                                cursor.execute(p_SQL, (ch[icount_param], idparametro,))
                                parameter_records = cursor.fetchall()
                                for parameter_row in parameter_records:
                                    if max_idparametro > parameter_row[1]:
                                        clayer_def = clayer_def + parameter_row[3] + "("
                                    else:
                                        clayer_def = clayer_def + parameter_row[3] + "),"
                            else:
                                clayer_def = clayer_def + sparameter + "),"
                                iconcate = 0
                    iconcate = 1
                icount_param += 1
            else:

                if idpadre != 0 or espadre != 0:
                    if espadre > 0:
                        clayer_def = clayer_def + ' ' + desparametro + '='
                        iconcate = 1
                    else:
                        if idtipodato == 5 and desparametro != '':
                            clayer_def = clayer_def + valor + "("
                        else:
                            clayer_def = clayer_def + valor + "),"
                else:
                    if idtipodato == 1:
                        iconcate = 0
                        if dimension == 1:  # SI ES UN PARAMETRO FIJO QUE MODIFICA LA DIMENSION
                            if prev_channels < int(sparameter):  # SI EL PARAMETRO ES MAYOR AL CANAL PREVIO
                                # print(1)
                                sparameter = str(prev_channels)
                    if idtipodato == 4:
                        sparameter = "'" + str(valor) + "'"
                        iconcate = 0

                    if idtipodato == 6:  # SI EL TIPO DE DATO ES MULTIPLO SE DEBE CONCATENAR LOS VALORES
                        iconcate = 0
                        sparameter = ''
                        p_SQL = " SELECT  b.idorden, b.idmodelodetallecapa, b.inicio, b.fin, a.base, " \
                                " a.idmodelocapaparametro " \
                                " FROM public.datos_modelo_TYPE(%s) a LEFT JOIN public.datos_parametro_type(%s) b " \
                                " ON a.idmodelodetallecapa = b.idmodelodetallecapa " \
                                " WHERE a.idmodelocapaparametro IN (SELECT idcapamultiplo " \
                                "                                   FROM public.modelocapaparametromultiplo " \
                                "                                   WHERE idmodelocapaparametro = %s)  " \
                                " ORDER BY idorden "
                        cursor.execute(p_SQL, (idmodelo, idmodelo, idmodelocapaparametro,))
                        multiple_records = cursor.fetchall()
                        for mutiple_row in multiple_records:
                            pinit = mutiple_row[2]  # INICIO DEL CROMOSOMA PARA LA CAPA EN CUESTION
                            pend = mutiple_row[3]  # FIN    DEL CROMOSOMA PARA LA CAPA EN CUESTION
                            base = mutiple_row[4]
                            array_multiple = array[pinit:pend]

                            # este es el original
                            p_SQL = " SELECT id , rangofin " \
                                    " FROM (SELECT(ROW_NUMBER() OVER())-1::INTEGER AS id, * " \
                                    "       FROM datos_modelo_TYPE(%s) " \
                                    "       WHERE idmodelodetallecapa = %s AND  (LENGTH(tipodato) > 0  OR " \
                                    "             rangofin = valor) " \
                                    "       ORDER BY idorden) as hlp " \
                                    " WHERE idmodelocapaparametro = %s; "
                            cursor.execute(p_SQL, (idmodelo, mutiple_row[1], mutiple_row[5],))
                            help_records = cursor.fetchall()
                            if base != '0':
                                if pinit == pend:
                                    sparameter = sparameter + "(2**" + str(help_records[0][1]) + ")*"
                                else:
                                    sparameter = sparameter + "(2**" + str(array_multiple[help_records[0][0]]) + ")*"
                            else:
                                if pinit == pend:
                                    sparameter = sparameter + str(help_records[0][1]) + "*"
                                else:
                                    sparameter = sparameter + str(array_multiple[help_records[0][0]]) + "*"
                        sparameter = sparameter[:-1]
                    if idtipodato == 7:
                        iconcate = 0
            if iconcate == 0:
                if base == '0':
                    if idtipodato == 7:
                        clayer_def = clayer_def + ' ' + desparametro + '= (1, ' + sparameter + '),'
                    else:
                        clayer_def = clayer_def + ' ' + desparametro + '=' + sparameter + ','
                else:
                    if idtipodato == 7:
                        clayer_def = clayer_def + ' ' + desparametro + '= (1, 2**' + sparameter + '),'
                    else:
                        clayer_def = clayer_def + ' ' + desparametro + '= 2**' + sparameter + ','

        clayer_def = clayer_def[:-1] + ')'
        return clayer_def

    def create_net(self, v_samples, v_chans, data, cursor, idmodelo, idred, stable_det_name):

        evaluate_create = 1

        tmp_idred = str(idred + 100000)
        tmp_idred = tmp_idred[1:]

        model_name = "./MODELS/" + (stable_det_name[8:len(stable_det_name) - 4]) + '/' + tmp_idred + '_model.json'
        weight_name = "./MODELS/" + (stable_det_name[8:len(stable_det_name) - 4]) + '/' + tmp_idred + '_ini_wgt.h5'

        input1 = Input(shape=(1, v_samples, v_chans))
        block = input1

        p_SQL = " SELECT descripcion AS lyr_des " \
                " FROM " + stable_det_name + \
                " WHERE idred = %s " \
                " ORDER BY idsecuencia "
        cursor.execute(p_SQL, (idred,))
        model_records = cursor.fetchall()
        for row in model_records:
            try:
                block = eval(row[0])(block)
            except ValueError as ve:
                print(ve)
                evaluate_create = 0
                break
        if evaluate_create == 1:
            self.model = Model(inputs=input1, outputs=block)
            self.model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['acc'])
            # serialize model to JSON
            model_json = self.model.to_json()
            with open(model_name, "w") as json_file:
                json_file.write(model_json)
            # serialize weights to HDF5
            self.model.save_weights(weight_name)

            self.model.summary()
            cnt_params = self.model.count_params()
        else:
            cnt_params = 9999999
        return cnt_params

    def train_bk(self, signal_train, labels_train, signal_valid, labels_valid, idred, stable_det_name):
        tmp_idred = str(idred + 100000)
        tmp_idred = tmp_idred[1:]
        weight_name = "./MODELS/" + (stable_det_name[8:len(stable_det_name) - 4]) + '/' + tmp_idred + '_end_wgt.h5'
        if self._created == False and self.model == None:
            errmsg = "[!] Error: classifier wasn't trained or classifier path is not precised."
            print(errmsg, file=sys.stderr)
            sys.exit(0)
        callbacks = [tf.keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=100,
                                                   verbose=1, mode='auto')]
        self.model.fit(signal_train, labels_train, batch_size=self.batch_size, epochs=self.epochs,
                       callbacks=callbacks, verbose=1, validation_data=(signal_valid, labels_valid))
        # serialize weights to HDF5
        self.model.save_weights(weight_name)
        self._trained = True

    def train(self, signal_train, labels_train, idred, stable_det_name):
        tmp_idred = str(idred + 100000)
        tmp_idred = tmp_idred[1:]
        weight_name = "./MODELS/" + (stable_det_name[8:len(stable_det_name) - 4]) + '/' + tmp_idred + '_end_wgt.h5'
        if self._created == False and self.model == None:
            errmsg = "[!] Error: classifier wasn't trained or classifier path is not precised."
            print(errmsg, file=sys.stderr)
            sys.exit(0)
        self.model.weights.clear()
        callbacks = [tf.keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=100,
                                                   verbose=1, mode='auto')]
        self.model.fit(signal_train, labels_train, batch_size=self.batch_size, epochs=self.epochs,
                       callbacks=callbacks, verbose=2, validation_split=0.10, shuffle=True)
        # serialize weights to HDF5
        self.model.save_weights(weight_name)
        self._trained = True


    def evaluate(self, signal_test, labels_test):
        cnt_params = self.model.count_params()
        pred = self.model.predict(signal_test)
        score = self.model.evaluate(signal_test, labels_test, verbose=0)
        test_labels = np.argwhere(labels_test == 1)[:, 1] + 1
        pred_labels = np.argmax(pred, axis=1) + 1
        kappa = cohen_kappa_score(test_labels, pred_labels)

        trainable_count = np.sum([K.count_params(w) for w in self.model.trainable_weights])
        non_trainable_count = np.sum([K.count_params(w) for w in self.model.non_trainable_weights])


        # print('PARAMETROS:', trainable_count, non_trainable_count)

        return cnt_params, kappa, score[1], non_trainable_count

    def release_gpu(self):
        K.clear_session()

    def reset_model(model):
        session = tf.compat.v1.keras.backend.get_session()
        for layer in model.model.layers:
            for v in layer.__dict__:
                v_arg = getattr(layer, v)
                if hasattr(v_arg, 'initializer'):
                    initializer_method = getattr(v_arg, 'initializer')
                    initializer_method.run(session=session)
                    print('reinitializing layer {}.{}'.format(layer.name, v))
        return model

    def reset_weights(model):
        session = tf.compat.v1.keras.backend.get_session()
        for layer in model.model.layers:
            if hasattr(layer, 'kernel_initializer'):
                layer.kernel.initializer.run(session=session)
        return model

    def cleanup_memory(self):
        K.clear_session()
        del self.combined
        del self.discriminator
        del self.generator
        gc.collect()
