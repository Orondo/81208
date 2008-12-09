#!/usr/bin/python
# -*- coding: latin-1 -*-

"""Script para asociar fichero MP3 con videoclips en YouTube publicado bajo licencia GPL"""

import sys
import getopt
import os
import string
from Queue import Queue
from threading import Thread

#estos son los modulos no estandar
try:
	import ID3
	#raise ImportError #debug
except ImportError:
	print """Este script necesita el modulo ID3, bájatelo de http://id3-py.sourceforge.net/ID3.tar.gz 
Copia el archivo ID3.py al mismo directorio donde tienes este script o instalalo con python setup.py"""
	sys.exit(3)

try:
	import gdata.youtube
	import gdata.youtube.service
except ImportError:	
	print """Este script necesita el módulo gdata-python-api, versión 1.2.3 o superior, bájatelo de http://code.google.com/p/gdata-python-client/downloads/list e instalalo con python setup.py
gdata depende de Element Tree, si usas Ubuntu descargalo con sudo apt-get install python-elementtree o descargalo desde http://effbot.org/downloads/#elementtree e instalalo con python setup.py	"""
	sys.exit(4)

def uso():
	print """81208.py: instrucciones de uso y ejemplos
Script en Python para asociar ficheros MP3 con su videoclip musical en YouTube.

Uso:	
	python 81208.py -f fichero1.mp3 fichero2.mp3 fichero3.mp3 
	Extraerá el título, autor y álbum de los ficheros fichero1.mp3,fichero2.mp3,fichero3.mp3 e imprimirá el enlace al videoclip en YouTube.

	python 81208.py directorioMP3
	Escaneará directorioMP3 e imprimirá el enlace a YouTube de todos los archivos MP3.

	python 81208.py -s [enlace|busqueda] directorioMP3 
	Con el argumento "enlace" (por defecto) imprime unicamente el enlace a YouTube, con "busqueda" imprime los terminos de la busqueda en YouTube, separados por comas, para concatenarlo con otro programa y asociar videoclip y cancion

	python 81208.py -u "Titulo de la canción":Autor "Otra canción":"Otro autor":Álbum
	Permite al usuario buscar en YouTube el videoclip sin tener el archivo MP3

	python 81208.py -t N [fichero|directorio|canción introducida por el usuario]
	En caso de que no encuentre el videoclip esta opción devuelve los primeros N resultados encontrados en YouTube. Si el parámetro es 0 devolverá el listado completo. 

	python 81208.py -e [simple|youtube] directorioMP3
	Permite especificar la estrategia de busqueda, por defecto "youtube". Dependiendo de la estrategia los resultados de la busqueda pueden variar. Con la estrategia simple (aún no implementada) busca la coincidencia exacta con el título y autor, la estrategia youtube no realiza ninguna transformacion sobre los resultados y puede que devuelva enlaces a videos de usuarios (covers) o a conciertos en vivo.

Ejemplo de uso:

	find /ruta/al/directorio/con/MP3 /otro/directorio/con/MP3 | grep "Un grupo o Autor" | python 81208.py -f | clive 

	Usa el script y clive para obtener los videoclips desde un listado cribado con grep.

	En caso de que el script no devuelva resultados ello puede deberse a que los archivos MP3 no tengan información ID3, más información en http://es.wikipedia.org/wiki/ID3
	"""

#funciones auxiliares para la transformacion de texto
isPuntuation = lambda x:x in string.punctuation 

def stripPuntuation(s):
	"""Elimina los signos de puntuacion"""
	tmp = []
	for letter in s:
		if not isPuntuation(letter):
			tmp.append(letter)
	return string.join(tmp,sep="")		
				
#funcion auxiliar para valorar si el resultado es el videoclip

def x(texto1, texto2):
	return True in map(lambda x:x in texto1,texto2)

def estrategia_simple(feed):
	"""toma un feed y busca la coincidencia exacta del titulo"""
	#Elimino los simbolos de puntuacion
	#TODO: valorar que tambien aparezca el album
	print "Estoy trabajando en ello"
	sys.exit(0)
	datosMP3 = []
	for dato in feed.datosMP3:
		datosMP3.append(string.upper(stripPuntuation(dato)))

	tituloyautor = list(set(string.upper(stripPuntuation(datosMP3[0] + datosMP3[1])))) #elimino duplicados: http://www.peterbe.com/plog/uniqifiers-benchmark, elimino puntuacion y paso a mayusculas

	candidatas = []
	for entrada in feed.entry:
		tituloentrada = string.upper(stripPuntuation(entrada.title.text))
		valoracion =  map(lambda x: x in tituloentrada,tituloyautor)
		print "tituloentrada:",tituloentrada,"titulo y autor",datosMP3[0] + datosMP3[1],valoracion,"valoracion.count(True)",valoracion.count(True),"len titulo y autor sin procesar:",len(datosMP3[0] + datosMP3[1]),"len tituloentrada:",len(tituloentrada),"len(tituloyautor)",len(tituloyautor),"balance True/False", valoracion.count(True),valoracion.count(False)
		#if count(False) * 5 < count 

		
def estrategia_youtube(feed):
	"""Devuelve el primer resultado encontrado por YouTube"""
	#asocio los datos del MP3 con el feed que devuelvo, para poder mostrarlos en la salida
	#este comportamiento debe darse en todas las estrategias
	resultado = feed.entry[0]
	resultado.datosMP3 = feed.datosMP3
	return resultado

estrategias = {"simple":estrategia_simple,"youtube":estrategia_youtube} #si quieres definir una nueva estrategia añadela aqui y define la funcion
estrategia = estrategia_youtube #establece el comportamiento por defecto del script


def procesar_directorio(directorio):
	"""Recorre los archivos MP3 del directorio"""
	resultado = []
	try:
		for fichero in os.listdir(directorio):
			#print procesar_ficheroMP3(directorio + os.sep + fichero) #debug
			resultado.append(procesar_ficheroMP3(directorio + os.sep + fichero))
	except OSError,err:
		print str(err)
	finally:
		return resultado

def procesar_ficheroMP3(fichero):
	"""Obtiene el titulo y autor del fichero MP3 indicado"""
	resultado = []
	try: 
		id3info = ID3.ID3(fichero)
		resultado = [id3info["TITLE"],id3info["ARTIST"],id3info["ALBUM"]] 
	except IOError,err:
		print str(err)
	except ID3.InvalidTagError:
		print fichero, "no es un archivo MP3 valido"
	finally:
		#print "procesar_ficheroMP3:",resultado #debug
		return resultado
		
def procesar_entrada(entrada):
	"""Busca en youtube la cancion indicada por el usuario con el formato TITULO:AUTOR o TITULO:AUTOR:ALBUM"""
	resultado = []
	#print "procesar_entrada",entrada,type(entrada) #debug
	if entrada.count(":") not in (1,2): 
		print "Formato incorrecto de entrada:", entrada
	else:
		resultado = [entrada.split(":")]
	return resultado

def ejecutarbusquedayprocesar():# solucion guarrilla para multihilo

	yt = gdata.youtube.service.YouTubeService()

	while True:
		try:
			busqueda = busquedas.get()
		except:
			continue #se produce un error raro al finalizar el script, con esto lo evito #debug

		feeds = []
		feeds.append(yt.YouTubeQuery(busqueda)) #aqui viene todo el bacalao con youtube	
		feeds[-1].datosMP3 = busqueda.datosMP3 #chapuza para asociar la busqueda al feed

		#compruebo ahora el parametro para evitar el procesamiento 
		#no se le aplica el formato de salida
		if entradas != -1:
			for feed in feeds:
				if entradas >= len(feed.entry) or entradas == 0:
					for entrada in feed.entry:
						print entrada.media.player.url
				else:
					for entrada in range(0,entradas):
						print feed.entry[entrada].media.player.url
		#finalmente el procesamiento
		for feed in feeds:
			try:
				formato_salida(estrategia(feed))
			except:
				pass #guarrada provisional
		busquedas.task_done()


procesamientos = [procesar_directorio,procesar_ficheroMP3,procesar_entrada]
procesamiento = procesar_directorio


def salida_busquedayenlace(feed):
	print "%s,%s" % (string.join(feed.datosMP3,sep=","),feed.media.player.url) #debug

def salida_enlace(feed):
	print feed.media.player.url

salidas = {"enlace":salida_enlace,"busqueda":salida_busquedayenlace}
formato_salida = salida_enlace

busquedas = Queue() #cola de busquedas global

def construye_busqueda(entrada):
	"""YouTubeQuery"""
	#TODO: Aqui se podria hacer un refinamiento de la busqueda
	#      quizas al incluir el ALBUM en la busqueda estamos eliminando resultados validos
	#print "construye_busqueda:",entrada #debug
	if entrada == []: raise Exception
	busqueda = gdata.youtube.service.YouTubeVideoQuery()

	busqueda.racy = "include"
	busqueda.orderby = "viewCount"
	busqueda.vq = string.join(entrada)
	busqueda.datosMP3 = entrada #un poco CHAPUZA
	#print busqueda #debug
	return busqueda

if __name__ == "__main__":

	try:
		opciones,argumentos = getopt.getopt(sys.argv[1:],'t:e:s:ufh')
	except getopt.GetoptError, err:
		print str(err)
		uso()
		sys.exit(1)

	#print opciones,argumentos #debug

	entradas = -1 #inicializco el numero de entradas que se mostraran con la opcion -t

	for opcion in opciones:
		if "-s" in opcion[0]:
			try:
				formato_salida = salidas[opcion[1]]
			except KeyError,err:
				print "El formato de salida %s no existe." % err
				sys.exit(2)
		if "-e" in opcion[0]:
			try:
				estrategia = estrategias[opcion[1]]
			except KeyError,err:
				print "La estrategia %s no existe." % err
				sys.exit(2)

		if "-h" in opcion[0]:
			uso()
			sys.exit(0)

		if "-f" in opcion[0]:
			procesamiento = procesar_ficheroMP3

		if "-u" in opcion[0]:
			procesamiento = procesar_entrada

		if "-t" in opcion[0]:
			try:
				entradas = int(opcion[1])
			except ValueError, err:
				print str(err)
				sys.exit(5)
		
	
	#si los argumentos estan vacios entender que pillamos la entrada estandar
	if argumentos == []:
		argumentos = sys.stdin.readlines()
		argumentos = [argumento[:-(len(os.linesep))] for argumento in argumentos]
		#-(len(os.linesep)) elimina los caracteres de salto de linea

	argumentos = list(set(argumentos)) #elimino los duplicados antes de procesarlos
	#print argumentos,len(argumentos) #debug

	resultados = []
	for argumento in argumentos:
		resultados.extend(procesamiento(argumento))
	#resultados = list(set(resultados))
	#print "resultados despues",resultados #debug

	
	hilodebusquedas = Thread(target = ejecutarbusquedayprocesar)
	hilodebusquedas.setDaemon(True)
	hilodebusquedas.start()

	for resultado in resultados:
		try:
			busquedas.put(construye_busqueda(resultado)) #gestiona todas las busquedas
		except Exception: 	
			pass

	busquedas.join()
	sys.exit(0)

