# -*- coding: utf-8 -*-

import os
import pickle
import socket

import hdf5storage as hdf5
import tensorflow.keras.backend as K
import numpy as np
import psycopg2
from tensorflow.keras.layers import Input
from platypus import *


import sys
import math

from tensorflow.keras import regularizers
from tensorflow.keras.constraints import max_norm
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Input, Conv2D, DepthwiseConv2D, SeparableConv2D, Activation, AveragePooling2D
from tensorflow.keras.models import Model

from random import seed
from random import randint

from UMA_Optimal_EEGNet_optim import EEGNetOptim


os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


v_main_pid = sys.argv[1]
v_idmodelo = sys.argv[2]
v_sujeto = sys.argv[3]
v_idnodo = sys.argv[4]
v_idgpu = sys.argv[5]
v_gpunumber = sys.argv[6]
v_item = sys.argv[7]
v_idexperimento = sys.argv[8]
if int(v_idgpu) > 0:
    os.environ["CUDA_VISIBLE_DEVICES"] = v_gpunumber
    print('GPU Nro.:', v_gpunumber, 'GPU Id.:', v_idgpu)


def _convert_constraint(x):
    if isinstance(x, Constraint):
        return x
    elif isinstance(x, (list, tuple)):
        return [_convert_constraint(y) for y in x]
    else:
        return Constraint(x)


class Problem(object):
    """Class representing a problem.

    Attributes
    ----------
    nvars: int
        The number of decision variables
    nobjs: int
        The number of objectives.
    nconstrs: int
        The number of constraints.
    function: callable
        The function used to evaluate the problem.  If no function is given,
        it is expected that the evaluate method is overridden.
    types: FixedLengthArray of Type
        The type of each decision variable.  The type describes the bounds and
        encoding/decoding required for each decision variable.
    directions: FixedLengthArray of int
        The optimization direction of each objective, either MINIMIZE (-1) or
        MAXIMIZE (1)
    constraints: FixedLengthArray of Constraint
        Describes the types of constraints as an equality or inequality.  The
        default requires each constraint value to be 0.
    """

    MINIMIZE = -1
    MAXIMIZE = 1

    def __init__(self, nvars, nobjs, nconstrs=0, function=None):
        """Create a new problem.

        Problems can be constructed by either subclassing and overriding the
        evaluate method or passing in a function of the form::

            def func_name(vars):
                # vars is a list of the decision variable values
                return (objs, constrs)

        Parameters
        ----------
        nvars: int
            The number of decision variables.
        nobjs: int
            The number of objectives.
        nconstrs: int (default 0)
            The number of constraints.
        function: callable (default None)
            The function that is used to evaluate the problem.
        """
        super(Problem, self).__init__()
        self.nvars = nvars
        self.nobjs = nobjs
        self.nconstrs = nconstrs
        self.function = function
        self.types = FixedLengthArray(nvars)
        self.directions = FixedLengthArray(nobjs, self.MINIMIZE)
        self.constraints = FixedLengthArray(nconstrs, "==0", _convert_constraint)

    def __call__(self, solution):
        """Evaluate the solution.

        This method is responsible for decoding the decision variables,
        invoking the evaluate method, and updating the solution.

        Parameters
        ----------
        solution: Solution
            The solution to evaluate.
        """
        problem = solution.problem

        p_SQL = " SELECT " \
                " CASE WHEN MAX(idred) IS NULL" \
                "   THEN  1 " \
                "   ELSE MAX(idred) + 1  END AS idred FROM " + stable_name
        cursor.execute(p_SQL, ())
        v_max_idred = cursor.fetchone()[0]
        print('IDred:', v_max_idred)

        inicio_formato = solution.variables[:]
        # print('Inicio Formato:   ', solution.variables[:])
        solution.variables[:] = [problem.types[i].decode(solution.variables[i]) for i in range(problem.nvars)]

        print('Inicio:   ', solution.variables[:])
        modelo = EEGNetOptim()

        input_height = 1
        # input_width = 5120
        input_width = 1206
        input_channels = 15

        prev_height = input_height
        prev_width = input_width
        prev_channels = input_channels

        iinit = 0
        ibeg_param = 0
        iend_param = 0
        eegnet_layers = []
        icount_types = 0

        global evaluate_eegnet
        evaluate_eegnet = 1

         #SELECCONA EL MODELO QUE QUEREMOS HACER EVOLUCIONAR

        p_SQL = " SELECT * " \
                " FROM datos_parametro_type(%s) "
        cursor.execute(p_SQL, (idmodelo,))
        vtypes_records = cursor.fetchall()
        tmp_idorden = vtypes_records[(len(vtypes_records)) - 1][0]
        idorden = 0
        tmp_idmodelodetalle = 0
        ctrl_type = 0

        for row in vtypes_records:

            dpt_idmodelodetalle = row[2]
            dpt_idmodelodetallecapa = row[3]
            dpt_evaluar = row[9]
            dpt_idcapa = row[10]

            if ctrl_type == 2:
                if tmp_idmodelodetalle == dpt_idmodelodetalle:
                    continue
                else:
                    ctrl_type = 0
                    tmp_idmodelodetalle = 0

            #CUANDO TIENE COMO RANDOM SI CUAL ES LA SIGUIENTE CAPA
            if idorden != 0:
                if row[0] < idorden:
                    icount_types += 1
                    continue

            icount_types += 1   #CONTADOR DE LOS VALORES RANDOM DEL CROMOSOMA

            dpt_idorden = row[0]

            iinit = row[7]    # INICIO DEL CROMOSOMA PARA LA CAPA EN CUESTION
            iend = row[8]     # FIN DEL CROMOSOMAP PARA LA CAPA EN CUESTION
            itot = row[5]     # TOTAL DE PARAMATROS DEL CROMOSOMA
            ibeg_param = iend_param + 1
            if dpt_idmodelodetallecapa == 0:
                itot = row[6]
                iend_param = iend_param + itot
            else:
                itot = row[5]
                iend_param = iend_param + itot
            array_values = solution.variables[iinit:iend]   # SELECCIONA LOS VALORES DEL CROMOSOMA PARA LA CAPA

            if dpt_idmodelodetallecapa == 0:
                idorden = dpt_idorden + array_values[0]
                ctrl_type = 1
                tmp_idmodelodetalle = dpt_idmodelodetalle
                continue

            clayer_def = modelo.script_layer(array_values, iend - iinit, ibeg_param, iend_param, cursor,
                                             solution.variables[:], idmodelo, prev_channels, dpt_idmodelodetalle,
                                             dpt_idmodelodetallecapa, dpt_idcapa)  # CREA EL SCRIPT DEL MODELO
            clayer_script = clayer_def

            # EN ESTE PUNTO VERIFICA SI VA CAMBIAR DE DIMENSIONES LAS CAPAS QUE EL CROMOSOMA TRAE INCORRECTO,
            # EN CASO QUE CAMBIE, SE PRUEBA CADA CAPA. SIRVE PARA QUE NO VEA CADA CAPA SI ES O NO FACTIBLE SU
            # DIMENSION, EN TEORIA PARA OPTIMIZAR EL TIEMPO.  var: cambia_dimension

            cambia_dimension = 0

            if (cambia_dimension == 0) and (v_max_idred > ga_population):
                # print('Capa:', icount_types, clayer_script)
                eegnet_layers.append(clayer_script)
            else:

                clayer_def = clayer_def + ('(test_input)')

                # print(clayer_def)

                # print(prev_height, prev_width, prev_channels)
                if dpt_evaluar == 1: # DEFINE SI LA CAPA SE DEBE EVALUAR CON SUS PARAMETROS O NO (LAS ULTIMAS CAPAS USUALMENTE NO)
                    icount = 0
                    array = []
                    ipos = 0
                    ival = 0
                    if len(array_values) > 0: # INGRESA SI EXISTE VALOR EN EL CROMOSOMA DE LA CAPA CORRESPONDIENTE
                        # ESTA CONSULTA SELECCIONA LOS PARAMETROS DE LA CAPA QUE VARIAN
                        p_SQL = ' SELECT(ROW_NUMBER() OVER()) - 1::INTEGER   AS item, idorden, idmodelodetallecapa, ' \
                                ' idmodelo, idcapa, dimension, base, rangoinicio, idtipodato, descapa, desparametro,' \
                                ' idparametro, idmodelodetalle ' \
                                ' FROM public.datos_modelo_type(%s) ' \
                                ' WHERE idmodelodetallecapa = %s AND LENGTH(tipodato) > 0 ' \
                                ' ORDER BY idorden '
                        cursor.execute(p_SQL, (idmodelo, dpt_idmodelodetallecapa,))
                        vars_records = cursor.fetchall()

                        for var_row in vars_records:

                            dmt_dimension = var_row[5]
                            if dmt_dimension == 1: #DETERMINA SI EL PARAMETRO AFECTA O NO LA DIMENSION DE LA CAPA
                                base = int(var_row[6])
                                idtipodato = var_row[8]
                                if idtipodato == 1 or idtipodato == 7: #DETERMINA SI EL PARAMETRO ES UN ARRAY O UNA TUPLA
                                    rangoinicio = int(var_row[7])
                                ipos = var_row[0] #INDICA LA POSICION DEL
                                icount += 1 #CONTABILIZA CANTIDAD DE PARAMTEROS QUE MODIFICAN LA DIMENSION DE UNA CAPA

                                dpt_idparametro = var_row[11]
                                p_SQL = " SELECT * " \
                                        " FROM public.selecciona_parametro_type(%s, %s, %s) " \
                                        " WHERE idparametro = %s "
                                cursor.execute(p_SQL, (idmodelo, dpt_idmodelodetalle, dpt_idcapa, dpt_idparametro))
                                titi_records = cursor.fetchall()
                                ipos = titi_records[0][0]
                                ival = array_values[ipos]
                                #ESTABLECE EL RANGO DE VALORES QUE PUEDE VARIAR EL PARAMETRO
                                tmp_rangoinicio = int(titi_records[0][4])
                                tmp_rangofin = int(titi_records[0][5]) + 1
                                array = list(range(tmp_rangoinicio, tmp_rangofin))

                    imodif = 0
                    # CICLO DONDE VERIFICA SI LA DIMENSION DE SALIDA ES LA CORRECTA PARA LA CAPA SIGUIENTE
                    # SI NO ES EL VALOR ADECUADO, LO MODIFICA.
                    while 'test_layer' not in locals():
                        try:
                            test_input = Input(shape=(prev_height, prev_width, prev_channels))
                            test_layer = eval(clayer_def)
                        except ValueError as ve:
                            print(ve)

                            # VERIFICA QUE LA CANTIDAD DE REDES GENERADAS NO SUPERE A LA POBLACION INICIAL, ESTO ES
                            # PORQUE SOLO LA POBLACION INCIAL VA A MODIFICAR LOS GENES QUE GENERAN EL ERROR EN LA PRIMERA
                            # VUELTA, Y A PARTIR DE LA SEGUNDA YA NO MODIFICARA LOS GENES
                            if v_max_idred > ga_population:
                                evaluate_eegnet = 0
                                break

                            if icount != 0:

                                array.remove(ival)  # ELIMINA DEL ARRAY EL VALOR QUE DA EL ERROR Y LO BUSCA AL AZAR
                                ival = random.choice(array)  #SELECCIONA AL AZAR EL VALOR DENTRO DEL ARRAY

                                array_values[ipos] = ival

                                clayer_def = modelo.script_layer(array_values, iend - iinit, ibeg_param, iend_param, cursor,
                                                                 solution.variables[:], idmodelo, prev_channels,
                                                                 dpt_idmodelodetalle, dpt_idmodelodetallecapa, dpt_idcapa)
                                clayer_script = clayer_def
                                # print(clayer_def)
                            clayer_def = clayer_def + ('(test_input)')

                    if evaluate_eegnet == 1:
                        if icount != 0:
                            solution.variables[iinit + ipos] = ival

                        out_height, out_width, out_channels = test_layer.shape.dims[1].value, test_layer.shape.dims[2].value, \
                                                              test_layer.shape.dims[3].value
                        test_layer = None
                    else:
                        break
                    try:
                        raise Exception
                    except Exception as test_layer:
                        pass

                    icount = 0
                    prev_height = out_height
                    prev_width = out_width
                    prev_channels = out_channels
                #     print(clayer_def)
                # else:
                #     print(clayer_def)

                if ctrl_type == 1:
                    ctrl_type = 2

                eegnet_layers.append(clayer_script)

                # SI MAS ARRIBA YA SE ESTABLECIO QUE NO DEBE EVALUAR Y QUE YA NO ES LA PRIMERA POBLACION (RANDOM)
                # ENTONCES ROMPE EL CICLO DE ARMADO DE LA RED
                if evaluate_eegnet == 0:
                    break

        # INSERTA EN LA TABLA DONDE SE GUARDAN EL CROMOSOMA CON SUS VALORES SELECCIONADOS
        global insert_script, idred
        stypes_values = "','".join(map(str, solution.variables))
        if len(stypes_values) > 0:
            stypes_values = "('" + stypes_values + "')"
        else:
            stypes_values = "('" + str(idmodelo) + "')"
        p_SQL = insert_script[0] + stypes_values + " RETURNING idred; "
        cursor.execute(p_SQL)
        idred = cursor.fetchone()[0]
        connection.commit()

        # NO GUARDA LA RED SI ES UNA MALA SOLUCION QUE NO HA PODIDO SER EVALUADA,  SI NO GUARDA EL DETALLE DE LA RED
        if evaluate_eegnet == 0:
            tmp_row = 'UNFEASIBLE NETWORK'
            print(tmp_row + ', NO Evaluar!!!!')
            p_SQL = " INSERT INTO " + stable_name + "_det  (idred, descripcion) VALUES (%s, %s) "
            cursor.execute(p_SQL, (idred, tmp_row))
            connection.commit()
        else:
            for row in eegnet_layers:
                p_SQL = " INSERT INTO " + stable_name + "_det  (idred, descripcion) VALUES (%s, %s) "
                cursor.execute(p_SQL, (idred, row))
                connection.commit()

        eegnet_layers = []
        print('IDred:', idred)
        print('Procesado:', solution.variables[:])

        self.evaluate(solution)

        solution.variables[:] = [problem.types[i].encode(solution.variables[i]) for i in range(problem.nvars)]

        # print('Procesado Formato:', solution.variables[:])
        print('\n\n')
        solution.constraint_violation = sum(
            [abs(f(x)) for (f, x) in zip(solution.problem.constraints, solution.constraints)])

        solution.feasible = solution.constraint_violation == 0.0
        solution.evaluated = True

    def evaluate(self, solution):
        """Evaluates the problem.

        By default, this method calls the function passed to the constructor.
        Alternatively, a problem can subclass and override this method.  When
        overriding, this method is responsible for updating the objectives
        and constraints stored in the solution.

        Parameters
        ----------
        solution: Solution
            The solution to evaluate.
        """
        if self.function is None:
            raise PlatypusError("function not defined")

        if self.nconstrs > 0:
            (objs, constrs) = self.function(solution.variables)
        else:
            objs = self.function(solution.variables)
            constrs = []

        if not hasattr(objs, "__getitem__"):
            objs = [objs]

        if not hasattr(constrs, "__getitem__"):
            constrs = [constrs]

        if len(objs) != self.nobjs:
            raise PlatypusError("incorrect number of objectives: expected %d, received %d" % (self.nobjs, len(objs)))

        if len(constrs) != self.nconstrs:
            raise PlatypusError(
                "incorrect number of constraints: expected %d, received %d" % (self.nconstrs, len(constrs)))

        solution.objectives[:] = objs
        solution.constraints[:] = constrs
        
def datasets(xsujeto, xbits):

    sujeto = xsujeto
    v_bits = xbits

    trainfile = './DATASET/TRAIN/' + sujeto + '.mat'
    f = hdf5.loadmat(trainfile)
    signal_train = f['eeg_signal'][:]

    trainclassfile = './DATASET/TRAIN/' + sujeto + '.mat'
    f = hdf5.loadmat(trainclassfile)
    labels = f['y'][:]
    labels = labels.flatten()
    labels_train = labels.T

    testfile = './DATASET/TEST/' + sujeto + '.mat'
    f = hdf5.loadmat(testfile)
    signal_test = f['eeg_signal'][:]

    testclassfile = './DATASET/TEST/' + sujeto + '.mat'
    f = hdf5.loadmat(testclassfile)
    labels = f['y'][:]
    labels = labels.flatten()
    labels_test = labels.T

    del labels

    labels_train = labels_train - 1
    labels_test = labels_test - 1

    # Reduccion de tamano de matriz, eliminar solapamiento
    x = range(19)
    v = 50
    w = 256

    new_signal_train = signal_train[0:256, :, :]
    new_signal_test = signal_test[0:256, :, :]

    for i in x:
        v_from = ((i + 2) * w) - v
        v_to = ((i + 2) * w)

        tmp_signal_train = signal_train[v_from:v_to, :, :]
        new_signal_train = np.concatenate((new_signal_train, tmp_signal_train), axis=0)

        tmp_signal_test = signal_test[v_from:v_to, :, :]
        new_signal_test = np.concatenate((new_signal_test, tmp_signal_test), axis=0)

    signal_train = new_signal_train
    signal_test = new_signal_test

    signal_train = np.asarray(signal_train).swapaxes(0, 2)
    signal_train = signal_train.swapaxes(1, 2)

    signal_test = np.asarray(signal_test).swapaxes(0, 2)
    signal_test = signal_test.swapaxes(1, 2)

    x_train = signal_train
    x_test = signal_test

    n_classes = len(np.unique(labels_train))

    labels_arr_train = np.zeros((labels_train.shape[0], n_classes))  # Labels array for FCN
    labels_arr_test = np.zeros((labels_test.shape[0], n_classes))  # Labels array for FCN

    for i in range(n_classes):
        labels_arr_train[:, i] = labels_train == i  # Generate binary labels array
        labels_arr_test[:, i] = labels_test == i

    x_train = np.reshape(x_train, [x_train.shape[0], 1, x_train.shape[1], x_train.shape[2]])
    x_test = np.reshape(x_test, [x_test.shape[0], 1, x_test.shape[1], x_test.shape[2]])

    if xbits == 0:
        x_train = x_train
        x_test = x_test
        labels_arr_train = labels_arr_train
        labels_arr_test = labels_arr_test
        signal_train = signal_train
        signal_test = signal_test

    if xbits == 32:
        x_train = x_train.astype('float32')
        x_test = x_test.astype('float32')
        labels_arr_train = labels_arr_train.astype('float32')
        labels_arr_test = labels_arr_test.astype('float32')
        signal_train = signal_train.astype('float32')
        signal_test = signal_test.astype('float32')
    if xbits == 64:
        x_train = x_train.astype('float64')
        x_test = x_test.astype('float64')
        labels_arr_train = labels_arr_train.astype('float64')
        labels_arr_test = labels_arr_test.astype('float64')
        signal_train = signal_train.astype('float64')
        signal_test = signal_test.astype('float64')

    return x_train, x_test, labels_arr_train, labels_arr_test, signal_train, signal_test


def eegnetoptim(vars):
    K.clear_session()

    cnt_params = 9999999
    kappa = -1
    acc = -1
    nt_params = -1

    tdate_ini = datetime.datetime.now()
    if evaluate_eegnet == 1 or idred <= ga_population:

        stable_det_name = stable_name + "_det"
        modelo = EEGNetOptim()
        modelo.epochs = cnn_epochs

        ch = [vars[i] for i in range(0, icount_types)]
        cnt_params = modelo.create_net(signal_train.shape[1], signal_train.shape[2], ch, cursor,
                                       idmodelo, idred, stable_det_name)

        if 0 < cnt_params <= cnn_max_parameters:
            modelo.train(x_train, labels_arr_train, idred, stable_det_name)
            [cnt_params, kappa, acc, nt_params] = modelo.evaluate(x_test, labels_arr_test)

        modelo.cleanup_memory()



    tdate_fin = datetime.datetime.now()

    p_SQL = " UPDATE " + stable_name + \
            " SET inicio = %s, fin = %s, parametros = %s, kappa= %s, acc = %s, mainpid = %s, " \
            "     idmodelo = %s, pid = %s, idnodo = %s, nt_parametros = %s, idgpu = %s "\
            " WHERE idred = %s;"
    cursor.execute(p_SQL, (tdate_ini, tdate_fin, cnt_params, float(kappa), float(acc), v_main_pid, idmodelo,  lpid, v_idnodo,
                           int(nt_params), v_idgpu, idred))
    connection.commit()

    print('Resultados', [cnt_params, kappa, acc])

    return [cnt_params, kappa]


def print_nondominant(algorithm):
    if algorithm.nfe % ga_population == 0:  # this assumes 100 is a multiple of your population size
        print(nondominated(algorithm.population))


try:

    idmodelo = v_idmodelo  # MODELO A OPTIMIZAR
    lpid = os.getpid()
    v_hostname = socket.gethostname()  # NODO EN EL QUE SE EJECUTA

    connection = psycopg2.connect(user="",
                                  password="",
                                  host="localhost",
                                  port="5432",
                                  database="")
    cursor = connection.cursor()

    # CREA EL NOMBRE DE LA TABLA DONDE SE GUARDAN LOS RESULTADOS DEL CROMOSOMA

    tmp_item = str(int(v_item) + 1000)
    tmp_item = tmp_item[1:]

    p_SQL = " SELECT abreviatura || '_' || SUBSTR(MD5(RANDOM()::TEXT), 0, 5) " \
            " FROM modelo " \
            " WHERE idmodelo = %s; "
    cursor.execute(p_SQL, (idmodelo,))
    tmp_name = cursor.fetchone()
    stable_name = 'results.GA'+tmp_item+'_N' + v_idnodo + '_GPU' + v_gpunumber + '_' + v_sujeto + '_' + tmp_name[0]
    sresul_name = stable_name[8:]
    print("Nombre Resultado:", sresul_name)

    # SAVE THE RESULTS
    file_results = sresul_name + '.pickle'

    p_SQL = " INSERT INTO public.ejecuciones (idexperimento, idnodo, item, tabla, archivo, mainpid, pid, idgpu) " \
            " VALUES  (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING idejecucion; "
    cursor.execute(p_SQL, (v_idexperimento, v_idnodo, v_item, stable_name, file_results, v_main_pid, str(lpid),
                           v_idgpu))
    v_idejecucion = cursor.fetchone()[0]
    connection.commit()

    # CONFIGURACION DEL ALGORITMO GENETICO Y DE LAS REDES NEURONALES
    p_SQL = ' SELECT idexperimento, ga_population, ga_nfe, cnn_max_parameters, cnn_epochs, ga_sbx, ga_pm, bits  ' \
            ' FROM public.experimentos ' \
            ' WHERE idexperimento = %s' \
            ' ORDER BY idexperimento '
    cursor.execute(p_SQL, (v_idexperimento,))
    tmp_setup = cursor.fetchone()
    ga_population = tmp_setup[1]
    ga_nfe = tmp_setup[2]
    cnn_max_parameters = tmp_setup[3]
    cnn_epochs = tmp_setup[4]
    ga_sbx = tmp_setup[5]
    ga_pm = tmp_setup[6]
    tmp_bits = tmp_setup[7]

    # DATASET SELECCIONADO
    x_train,  x_test, labels_arr_train, labels_arr_test, signal_train, signal_test = datasets(v_sujeto, tmp_bits)

    # CREA LA CARPETA DONDE SE GUARDAN LOS PESOS DE LAS REDES
    os.mkdir("./MODELS/"+sresul_name, 0o777)

    # CREA LA TABLA DONDE SE ALMACENAN LOS CROMOSOMAS Y LOS RESULTADOS DE LA EVALUACION
    cursor.callproc('create_table', [stable_name, idmodelo, ])
    insert_script = cursor.fetchone()
    connection.commit()

    # CREA LOS COMPONENTES DEL CROMOSOMA A PARTIR DEL MODELO DISENADO PREVIAMENTE
    p_SQL = " SELECT MAX(tipodato)::CHARACTER VARYING(100) AS tipodato " \
            " FROM public.datos_modelo_type(%s) " \
            " WHERE LENGTH(tipodato) > 0 " \
            " GROUP BY idmodelodetalle, idparametro, desparametro, rangoinicio, rangofin " \
            " ORDER BY idmodelodetalle, idparametro "
    cursor.execute(p_SQL, (idmodelo,))
    types_records = cursor.fetchall()

    from platypus.types import Integer
    icount_types = 0
    array_types = []
    for row in types_records:
        icount_types += 1
        array_types.append(eval(row[0]))

    # DECLARACION DEL PROBLEMA A OPTIMIZAR
    problem = Problem(icount_types, 2)  # CANTIDAD DE VARIABLES DE DECISION Y OBJETIVOS
    problem.types[:] = array_types  # VARIABLES DE DECISION

    # DECLARACION DE FITNESS FUNCTION
    problem.function = eegnetoptim

    # DECLARACION DE OBJETIVOS CONTRAPUESTOS
    problem.directions[0] = Problem.MINIMIZE  # PARAMETROS
    problem.directions[1] = Problem.MAXIMIZE  # KAPPA

    ########################
    # EJECUTA EL EVOLUTIVO #
    ########################

    # ga_SBX:Simulated Binary Crossover
    # ga_PM:Polynomial Mutation
    # ga_NFE = population_size * generations


    print('ALGORITMO GENETICO')
    ga_date_ini = datetime.datetime.now()
    algorithm = NSGAII(problem,  variator=CompoundOperator(SBX(0.75, 20.0), HUX(), PM(0.25, 20.0),
                                                            BitFlip()), population_size=ga_population)
    algorithm.run(ga_nfe)
    ga_date_end = datetime.datetime.now()
    print('GA->Tiempo de Ejecución:', ga_date_end - ga_date_ini)

    #######################
    # GUARDA DATOS DEL GA #
    #######################
    p_SQL = " UPDATE public.ejecuciones" \
            " SET  ga_ini         = %s,  " \
            "      ga_end         = %s,  " \
            "      ga_population  = %s,  " \
            "      ga_nfe         = %s   " \
            " WHERE idejecucion = %s     "
    cursor.execute(p_SQL, (ga_date_ini, ga_date_end, ga_population, ga_nfe, v_idejecucion))
    connection.commit()

    #########################
    # GUARDA LAS SOLUCIONES #
    #########################
    print('Inicio de Guardado de Soluciones')
    arr_non_dominated = []  # ARRAY PARA EL CODO DEL FRENTE DE PARETO DE LAS SOLUCIONES NO DOMINADAS
    arr_nd_param = []
    arr_nd_kappa = []

    feasible_solutions = [s for s in algorithm.result if s.feasible]
    nondominated_solutions = nondominated(algorithm.result)

    print('Guardado de Soluciones: FACTIBLES')
    for solution in feasible_solutions:
        v_parametros = solution.objectives[0]
        v_kappa = solution.objectives[1]
        p_SQL = " INSERT INTO public.soluciones (idejecucion, parametros, kappa) VALUES " \
                " (%s, %s, %s)  "
        cursor.execute(p_SQL, (v_idejecucion, v_parametros, v_kappa))
        connection.commit()

    print('Guardado de Soluciones: NO DOMINADAS')
    for solution in nondominated_solutions:
        v_parametros = solution.objectives[0]
        v_kappa = solution.objectives[1]
        p_SQL = " INSERT INTO public.solucionesnd (idejecucion, parametros, kappa) VALUES " \
                " (%s, %s, %s)  "
        cursor.execute(p_SQL, (v_idejecucion, v_parametros, v_kappa))
        connection.commit()

    print('Ordenado de Soluciones: NO DOMINADAS')
    
    p_SQL = " SELECT idejecucion, parametros, kappa " \
            " FROM  public.solucionesnd " \
            " WHERE idejecucion = %s " \
            " GROUP BY idejecucion, parametros, kappa " \
            " ORDER BY idejecucion, parametros ASC; "
    cursor.execute(p_SQL, (v_idejecucion,))
    solucionesnd = cursor.fetchall()

    for row in solucionesnd:
        print(row[0], row[1], row[2])
        arr_nd_param.append(row[1])
        arr_nd_kappa.append(row[2])

    ############################################
    # ACTUALIZA EL ESTADO DE LA GPU O EL NODO  #
    ############################################
    if int(v_idgpu) > 0:
        # Actualiza el estado de la GPU
        cursor.execute(" UPDATE gpus "
                       " SET utilizado = 0 "
                       " WHERE idgpu = " + str(v_idgpu))
    else:
        # Actualiza el estado del nodo
        cursor.execute(" UPDATE public.nodos "
                       " SET utilizado = 0 "
                       " WHERE idnodo = " + str(v_idnodo))
    connection.commit()

    with open('./RESULTS/'+file_results, "wb") as f:
        pickle.dump(algorithm, f, pickle.HIGHEST_PROTOCOL)

except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    # closing database connection.
    if (connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
