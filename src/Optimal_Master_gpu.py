import psycopg2
import os

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:

    imainpid = os.getpid()

    os.chdir('')

    connection = psycopg2.connect(user="",
                                  password="",
                                  host="",
                                  port="",
                                  database="")

    cursor = connection.cursor()

    launchDir = ""
    v_main_pid = str(os.getpid())

    #el valor de cejec en el item es cejec + 1
    cejec = 200
    while True:
        # VERIFICA CUANTOS EXPERIMENTOS CON EJECUCIONES PENDIENTES EXISTEN
        cursor.execute(" SELECT COUNT(*) AS cantidad "
                       " FROM public.experimentos "
                       " WHERE ejecuciones < total ")
        v_pendiente = cursor.fetchone()[0]
        # print("Pendientes:", v_pendiente)

        if v_pendiente > 0:
            v_idparallel = 1  # POR DEFECTO SE DISTRIBUYE LA EJECUCION EN LOS NODOS DISPONIBLES
            # VERIFICA EL EXPERIMENTO QUE TIENE EJECUCIONES PENDIENTES
            p_SQL = ' SELECT idexperimento, idmodelo, idmuestra, ejecuciones, total, idparallel_level ' \
                    ' FROM public.experimentos ' \
                    ' WHERE ejecuciones < total ' \
                    ' ORDER BY idexperimento ' \
                    ' LIMIT 1 '
            cursor.execute(p_SQL)
            vars_exp = cursor.fetchall()
            for var_exp in vars_exp:
                v_idexperimento = var_exp[0]
                v_idmodelo = var_exp[1]
                v_idmuestra = var_exp[2]
                v_idparallel = var_exp[5]
                # SELECCIONA QUE DATASET SERA UTILIZADO
                cursor.execute(" SELECT descripcion AS sujeto "
                               " FROM public.muestras "
                               " WHERE idmuestra = " + str(v_idmuestra))
                v_sujeto = cursor.fetchone()[0]

            # print("Sujeto:", v_sujeto)

            # VERIFICA LOS NODOS LIBRES PARA LA EJECUCION
            if v_idparallel == 1:
                cursor.execute(" SELECT COUNT(*) AS cantidad "
                               " FROM public.nodos "
                               " WHERE activo = 1 AND utilizado = 0  ")

            # VERIFICA LAS GPUS LIBRES PARA LA EJECUCION
            if v_idparallel == 2:
                cursor.execute(" SELECT COUNT(*) AS cantidad "
                               " FROM public.gpus "
                               " WHERE activo = 1 AND utilizado = 0  ")
            v_hw_disp = cursor.fetchone()[0]
            # print("Nodos Libres:", v_hw_disp)

            if v_hw_disp > 0:

                if v_idparallel == 1:
                    p_SQL = ' SELECT a.idnodo, a.descripcion as hostname, -1 AS idgpu, '' AS gpu_name, -1 as number, ' \
                            ' a.utilizado, a.activo ' \
                            ' FROM public.nodos a ' \
                            ' WHERE a.activo = 1 AND a.utilizado = 0 ' \
                            ' ORDER BY a.idnodo ' \
                            ' LIMIT 1 '
                if v_idparallel == 2:
                    p_SQL = ' SELECT a.idnodo, b.descripcion as hostname, a.idgpu, a.name AS gpu_name, ' \
                            ' a.number, a.utilizado, a.activo ' \
                            ' FROM public.gpus a LEFT JOIN public.nodos b ON a.idnodo = b.idnodo ' \
                            ' WHERE a.activo = 1 AND a.utilizado = 0 ' \
                            ' ORDER BY idgpu ' \
                            ' LIMIT 1 '

                cursor.execute(p_SQL)
                vars_hw = cursor.fetchall()

                for var_row in vars_hw:

                    v_idnodo = var_row[0]
                    v_hostname = var_row[1]
                    v_idgpu = var_row[2]
                    v_gpuname = var_row[3]
                    v_gpunumber = var_row[4]

                    # print("Nodo a Utilizar:", v_idnodo)
                    if v_idparallel == 1:
                        # Actualiza el estado del Nodo
                        cursor.execute("UPDATE nodos SET utilizado = 1 where idnodo = " + str(v_idnodo))
                    if v_idparallel == 2:
                        # Actualiza el estado de la GPU
                        cursor.execute("UPDATE gpus SET utilizado = 1 where idgpu = " + str(v_idgpu))
                    connection.commit()

                    cejec += 1

                    v_command = "cd " + launchDir + ";" + " nohup python3 UMA_Optimal_Worker_gpu.py " + v_main_pid \
                                + ' ' + str(v_idmodelo) + ' ' + v_sujeto + ' ' + str(v_idnodo) + ' ' + \
                                str(v_idgpu) + ' ' + str(v_gpunumber) + ' ' + str(cejec) + ' ' + \
                                str(v_idexperimento) + ' ' + "&> ./NOHUP/nohup" + str(cejec) + ".out &"
                    print(v_command)
                    os.system(v_command)
                    # Actualiza la cantidad de experimentos
                    cursor.execute(" UPDATE public.experimentos SET ejecuciones = ejecuciones + 1 "
                                   " WHERE idexperimento = " + str(v_idexperimento))
                    connection.commit()
        if v_pendiente == 0:
            break

    p_SQL = ' SELECT idexperimento, idmodelo, idmuestra, ejecuciones, total' \
            ' FROM public.experimentos ' \
            ' WHERE ejecuciones < total ' \
            ' ORDER BY idexperimento ' \
            ' LIMIT 1 '
    cursor.execute(p_SQL)
    vars_exp = cursor.fetchall()
    for var_row in vars_exp:
        print(var_row[1])

    p_SQL = ' SELECT idnodo, descripcion, utilizado, activo ' \
            ' FROM public.nodos ' \
            ' WHERE activo = 1 ' \
            ' ORDER BY idnodo'
    cursor.execute(p_SQL)
    vars_node = cursor.fetchall()
    for var_row in vars_node:
        print(var_row[1])


except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    # closing database connection.
    if (connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
