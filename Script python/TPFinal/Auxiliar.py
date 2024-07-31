import numpy as np
import pandas as pd
from matplotlib import pyplot as plt



def generar_escalera(LSB,num_steps,time_step):

    # Definir los parámetros

    # Generar el tiempo
    time = np.arange(0, (num_steps +2)* time_step, time_step)

    # Generar los valores de la señal escalera
    values = np.arange(0, num_steps +2) * (2*LSB)-((num_steps)*LSB)

    # Asegurarse de que los tiempos y valores tengan la misma longitud
    time = time[:len(values)]
    time=time

    # Crear la figura

    # Graficar la señal escalera
    plt.step(time, values, where='post', linestyle='-', linewidth=0.5, color='r', label='Señal Escalera')



    return time,values


def IDNL(nombre_archivo):



    time_step = 100e-9
    LSB = 1.225e-3
    num_steps = 63
    offset=85e-9


    data = pd.read_csv(nombre_archivo, skiprows=2, sep='\s+',index_col=None)
    num_columns = data.shape[1]

# Iterar sobre todas las columnas a partir de la segunda (índice 1)
    for t in range(1, num_columns):
        x = data.iloc[:, 0]  # Primera columna
        y = data.iloc[:, t]  # Columna i
        print(f"-------------------Columna {t} del archivo---------------",t)



       #x_min = 0.9e-8
        #x_max = 6.452e-7
        x_min = 5e-10
        x_max = 7e-6
        filtered_data = data[(x >= x_min) & (x <= x_max)]

        x_filtered = filtered_data.iloc[:, 0]
        y_filtered = filtered_data.iloc[:, t]
        x_filtered=x_filtered - 5e-8

        plt.figure()
        plt.plot(x_filtered , y_filtered, linestyle='-', color='b', label='Datos DAC')



        tiempo, escalera = generar_escalera(LSB, num_steps, time_step)


        tiempos_guardados = []
        valores_guardados = []
        contador=0
        ultimo_tiempo=0
        tiempo_inicial=0

        primer_dato=True
        k=0
        diferencia=[]

        for i in range(len(x_filtered)-1):
            tiempo_actual = x_filtered.iloc[i+1]  # Acceder al elemento i de x_filtered
            if(primer_dato==True and tiempo_actual>=offset):
                primer_dato=False
                tiempos_guardados.append(x_filtered.iloc[i])
                valores_guardados.append(y_filtered.iloc[i])
                k=k+1
                ultimo_tiempo = tiempo_actual

            elif (tiempo_actual >= k*time_step+offset):
                if(i<len(y_filtered)-1):
                    valor_interpolado = y_filtered.iloc[i-1] + (tiempo_actual - x_filtered.iloc[i-1]) * (y_filtered.iloc[i+1] - y_filtered.iloc[i-1]) / (x_filtered.iloc[i+1] - x_filtered.iloc[i-1])

                    tiempos_guardados.append(tiempo_actual)
                    valores_guardados.append(valor_interpolado)

                    ultimo_tiempo = tiempo_actual
                    diff =   escalera[k]-valor_interpolado
                    print("Resta=",escalera[k],"-",valor_interpolado)
                    diferencia.append(diff)
                    k=k+1

        tiempos_guardados = np.array(tiempos_guardados)
        valores_guardados = np.array(valores_guardados)

        plt.plot(tiempos_guardados, valores_guardados, marker='o', linestyle='', color='g', markersize=5)
        plt.grid(True)
        plt.tight_layout()
        plt.title('Salida del DAC')
        plt.xlabel('Codigo de entrada')
        plt.ylabel('Valor analógico de salida')
        plt.legend()
        plt.show()


        ##--------------------INL
        plt.figure()
        bits = np.arange(len(diferencia))  # Valores de x de 0 a 63
        plt.step(bits, np.array(diferencia)/(2*LSB), where='post', linestyle='-', linewidth=0.5, color='b')

        plt.title('INL')
        plt.xlabel('Codigo de entrada')
        plt.ylabel('Diferencia entre valor ideal y real (LSB)')
        plt.legend()
        plt.grid(True)
        plt.show()
        inl=np.array(diferencia)/(2*LSB)
        print("INL en funcion del codigo",inl)


        indice_max = np.argmax(abs(inl))

        max_inl = abs(inl[indice_max])
        #tiempo_max_inl = tiempos_guardados[indice_max]

        #codigo_max_inl=entero_cercano = round(tiempo_max_inl / time_step)

        print("El INL max es =",max_inl,"LSB y ocurre para el codigo",indice_max)


    ##---------------Offset

        print("OFFSET =",-diferencia[0],"V")
        print("OFFSET =",100*(-diferencia[0])/(2*LSB),"%LSB")

        ##---------------DNL

        dnl=np.zeros(len(valores_guardados)-1)
        for i in range(len(valores_guardados)-1):
            print("DNL=",valores_guardados[i+1],"-",escalera[i],"=",(valores_guardados[i+1]-escalera[i])/(2*LSB)-1)
            dnl[i]= (valores_guardados[i+1]-escalera[i])/(2*LSB)-1

        #print(dnl)

        plt.figure()
        #plt.plot(dnl[1:-1], marker='o', linestyle='-', color='g', markersize=5)
        plt.step(1+ bits, dnl, where='post', linestyle='-', linewidth=0.5, color='b')

        plt.title('DNL')
        plt.xlabel('Codigo de entrada')
        plt.ylabel('LSB')
        plt.grid(True)
        plt.show()


        indice_max_dnl = np.argmax(abs(dnl))
        max_dnl = dnl[indice_max_dnl]
        #max_dnl[V]
        print("El DNL max es =",max_dnl,"y ocurre para el codigo",indice_max_dnl+1)


    ##---------Ganancia

        #Calcula la itnerpolacion de los datos
        #Como los valores que guardo estan desfasados en el tiempo me creo un vector ideal
        x = np.linspace(offset, offset+time_step*63, len(valores_guardados))

        coefficients = np.polyfit(x,valores_guardados, 1)
        p = np.poly1d(coefficients)
        y_fit = p(x)
        #Ideal sope= [- 64*Iref*Rsense -( 64*Iref*Rsense ) ] / [ 2^6]=2.45mV=2*LSB          (EN REALIDAD SERIA LSB=2.45)

        print("Ganancia de error DAC = ideal - actual=",2*LSB*1000,"[mV/digito]-",1000*p[1]*time_step,"[mV/digito]","=",2*LSB*1000-1000*p[1]*time_step)
        print("Ganancia de error DAC [dB]=",20*np.log(abs(2*LSB*1000-1000*p[1]*time_step)))
        print("Ganancia de error DAC [%]=",(2*LSB*1000-1000*p[1]*time_step)*100,"%")

        plt.figure()
        plt.plot(tiempos_guardados,valores_guardados, 'bo', label='Datos originales')
        plt.plot(x, y_fit, 'r-', label='Recta ajustada')
        plt.title('Ajuste lineal (Interpolación lineal)')
        plt.xlabel('Codiog de entrada')
        plt.ylabel('Valor analógico de salida')
        plt.legend()
        plt.grid(True)
        plt.show()