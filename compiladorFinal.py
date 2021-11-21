"""
Nombre: Alejandro Tejada
Curso: Diseño Compiladores
Fecha: noviembre 2021
Programa: compiladorFinal.py
Propósito: Esta clase aloja la logica del compilador final
V 2.0
"""

from os import name
from mainSemantic import Compilar
from mainIntermedio import CompilarIntermedio
from ARMGenerator import *
import pickle
from pprint import pp, pprint


class Compilador_Final():

    def __init__(self) -> None:
        """
        Variables iniciales finales
        """
        self.codigoIntermedio = []
        self.metodosCodigoIntermedio = {}
        self.sizeMetodoActual = 0
        self.metodoActual = ""
        self.primerMetodo = ""
        self.readIntermediateCode()
        self.limpiarCodigo()
        self.headerPlaced = False
        # variables globales para los registros
        self.descriptor_reg = {
            'R0': [],
            'R1': [],
            'R2': [],
            'R3': [],
            'R4': [],
            'R5': [],
            'R6': [],
            'R7': [],
            'R8': [],
            'R9': [],
            'R10': [],
        }
        # Descriptor de direccciones
        self.descriptor_dir = {}
        # algunos operandos
        self.bool_operands = {
            '<=': 'bge',
            '>=': 'ble',
            '!=': 'bne',
            '==': 'beq',
            '<': 'bgt',
            '>': 'blt',
        }
        self.iterarCodigoIntermedio()

    def readIntermediateCode(self):
        infile = open("codigoIntermedioFinal", 'rb')
        self.codigoIntermedio = pickle.load(infile)
        infile2 = open("codigoMetodos", 'rb')
        self.metodosCodigoIntermedio = pickle.load(infile2)

    def limpiarCodigo(self):
        arrayTripleta = []
        for tripleta in self.codigoIntermedio:
            cont = 0
            for x in tripleta:
                if x != ' ':
                    tripLimpia = tripleta[cont:len(tripleta)]
                    arrayTripleta.append(tripLimpia)
                    break
                cont += 1

        innerArray = []
        for x in arrayTripleta:
            if '\n' in x:
                arraySplit = x.split('\n')
                for y in arraySplit:
                    if y != '' and y != ' ' and y != '   ':
                        innerArray.append(y)
            else:
                innerArray.append(x)

        for i in range(len(innerArray)):
            valor = innerArray[i]
            cont = 0
            for j in valor:
                if j.isalpha():
                    innerArray[i] = valor[cont:len(valor)]
                    break
                cont += 1

        self.codigoIntermedio = innerArray

    def iterarCodigoIntermedio(self):
        print("X")
        codigoAssemblerFinal = ""
        # isntancia del ARMG generator
        generadorCodigoARM = ARGCodigoGenerador()
        for x in self.codigoIntermedio:
            # condicion cuando iniciamos la definicion o es un DEF main
            if ('DEF' in x) and ('END DEF' not in x):
                # significa que es una definicion
                nameFuncion = x.replace('DEF ', '')
                nameFuncion = nameFuncion.replace(':', '')
                self.metodoActual = nameFuncion
                # buscamos su size en el dict y ahora ya lo tenemos
                for llave, valor in self.metodosCodigoIntermedio.items():
                    if(llave == nameFuncion):
                        self.sizeMetodoActual = valor
                # ahora miramos si es un header GLOBAL o solo uno extra
                if(self.headerPlaced == False):  # no han puesto el header, primero método que nos topamos
                    # generamos el encabezado inicial
                    self.headerPlaced = True
                    self.primerMetodo = nameFuncion
                    codigoAssemblerFinal += generadorCodigoARM.construirEncabezado(
                        nameFuncion)
                    # alocamos el tamaño de la funcion
                    codigoAssemblerFinal += generadorCodigoARM.alocarEspacioMetodo(
                        self.sizeMetodoActual)
                else:
                    # si es una declaracion nueva aparte de la global
                    codigoAssemblerFinal += generadorCodigoARM.construirFuncionNueva(
                        nameFuncion)
                    # alocamos el tamaño de la funcion
                    codigoAssemblerFinal += generadorCodigoARM.alocarEspacioMetodo(
                        self.sizeMetodoActual)

            elif('END DEF' in x):
                pass
            else:  # de lo contrario es una tripleta
                # obtenemos los registros
                codigo, registros, elementos = self.getReg(x)
                codigoAssemblerFinal += codigo
                if('+' in x) or ('*' in x) or ('-' in x):  # si es una operacion x= a + b
                    if('+' in x):  # si es una suma
                        codigoAssemblerFinal += generadorCodigoARM.construirSuma(
                            registros)
                    if('*' in x):  # si es una suma
                        codigoAssemblerFinal += generadorCodigoARM.construirMultiplicacion(
                            registros)
                    if('-' in x):  # si es una suma
                        codigoAssemblerFinal += generadorCodigoARM.construirResta(
                            registros)
                    # actualizamos
                    self.descriptor_reg[registros[0]] = [elementos[0]]
                    self.descriptor_dir[elementos[0]] = [registros[0]]
                    for llave, valor in self.descriptor_dir.items():
                        if registros[0] in valor and llave != elementos[0]:
                            indice = valor.index(registros[0])
                            self.descriptor_dir[llave].pop(indice)
        print(self.getReg("t0 = fp[4] + fp[8]"))
        print(self.getReg("fp[0] = t0"))

        print("-------------CODIGO ASSEMBLER FINAL----------")
        print()
        print(codigoAssemblerFinal)

    def getPositionSP(self, variable):
        if variable[0] == "f":  # es una variable Local
            val = str(variable[3:-1])
            if val.isnumeric():
                inst = f'[sp, #{val}]'
                return inst
            else:
                return variable

    def getReg(self, inst):
        inst = str(inst).strip().replace("\t", "").replace(" ", "")
        flagop = False
        op = ""
        operators = ['+', '-', '*', '/', '%']
        code = ""
        regs = ['', '', '']
        case3 = False
        elements = []
        # Verificar si es una operacion u asignacion
        for x in operators:
            if x in inst:
                flagop = True
                op = x

        llaves = self.descriptor_dir.keys()

        if flagop:  # si la instruccion es tripleta
            pos_eq = inst.find("=")
            pos_op = inst.find(op)
            x = inst[:pos_eq]
            y = inst[pos_eq+1:pos_op]
            z = inst[pos_op+1:]
            if x not in llaves:
                self.descriptor_dir[x] = [] if 't' in x else [x]
            if y not in llaves:
                self.descriptor_dir[y] = [] if 't' in y else [y]
            if z not in llaves:
                self.descriptor_dir[z] = [] if 't' in z else [z]
            print("Val1 ", x)
            print("Val2 ", y)
            print("Val3 ", z)
            elements = [x, y, z]
            case3 = True
            # valor y
            # Revision de caso 1 y 2
            for key, value in self.descriptor_reg.items():
                if y in value:
                    print("Entro al caso 1, no se hace nada")
                    print("Reg ", key)
                    regs[1] = key
                    case3 = False
                    break
                if y not in value:
                    if len(value) == 0:
                        print("Reg ", key)
                        self.descriptor_reg[key] = [
                            y]  # se ingresa al registro
                        self.descriptor_dir[y].append(key)
                        code += f"\tldr {key}, {self.getPositionSP(y)}\n"
                        regs[1] = key
                        case3 = False
                        break
            if case3:  # No encontro primeros casos
                for key, value in self.descriptor_dir.items():
                    # ingresar casos de caso 3
                    if len(value) > 1:
                        index = 0
                        for val in value:
                            if 'R' in val:
                                break
                            index += 1
                        tempR = self.descriptor_dir[key].pop(
                            index)  # se quita el registro
                        self.descriptor_reg[tempR] = key
                        code += f"\tldr {tempR}, {self.getPositionSP(y)}\n"
                        regs[1] = key
                        break

            case3 = True
            # valor z
            # Revision de caso 1 y 2
            for key, value in self.descriptor_reg.items():
                if z in value:
                    print("Entro al caso 1, no se hace nada")
                    print("Reg ", key)
                    regs[2] = key
                    case3 = False
                    break
                if z not in value:
                    if len(value) == 0:
                        print("Reg ", key)
                        self.descriptor_reg[key] = [
                            z]  # se ingresa al registro
                        self.descriptor_dir[z].append(key)
                        code += f"\tldr {key}, {self.getPositionSP(z)}\n"
                        regs[2] = key
                        case3 = False
                        break
            if case3:  # No encontro primeros casos
                for key, value in self.descriptor_dir.items():
                    # ingresar casos de caso 3
                    if len(value) > 1:
                        index = 0
                        for val in value:
                            if 'R' in val:
                                break
                            index += 1
                        tempR = self.descriptor_dir[key].pop(
                            index)  # se quita el registro
                        self.descriptor_reg[tempR] = key
                        code += f"\tldr {tempR}, {self.getPositionSP(z)}\n"
                        regs[2] = key
                        break

            # valor x
            for key, value in self.descriptor_reg.items():  # Caso 1
                if x in value:
                    regs[0] = key
                    break

            if regs[0] == '':  # No se cumple el caso 1
                regs[0] = regs[1]

            self.descriptor_dir[x].append(regs[0])
            self.descriptor_reg[regs[0]] = [x]

        else:  # si la instruccion es una asignacion
            pos_eq = inst.find("=")
            x = inst[:pos_eq]
            y = inst[pos_eq+1:]
            elements = [x, y]
            keysDir = self.descriptor_dir.keys()
            if x not in keysDir:
                self.descriptor_dir[x] = [] if 't' in x else [x]
            if y not in keysDir:
                self.descriptor_dir[y] = [] if 't' in y else [y]
            print("Val1 ", x)
            print("Val2 ", y)
            tempReg = self.descriptor_dir[y]
            regy = ""
            # Encontrar registro de Y
            for ele in tempReg:
                if "R" == ele[0]:
                    regy = ele

            # Agregar x al descriptor de registro Ry
            self.descriptor_reg[regy].append(x)
            self.descriptor_dir[x] = [x]
            regs[0] = regy
            regs[1] = regy
            code = f"\tstr {regy}, {self.getPositionSP(x)}\n"

        return code, regs, elements


compiladorsito = Compilador_Final()
print()
print("-----------------------------")
