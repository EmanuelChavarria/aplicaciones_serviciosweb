numero = 12
print(type(numero))

listas = [1,2,3, True, "Hola"]
print(listas)

def crear_Clase(lista: list):
    return [1,2,3,4]
variable = crear_Clase(listas)
print(variable)

class Ciudades:
    def __init__(self, lugar: str, habitantes: int):
        self.lugar = lugar
        self.habitantes = habitantes
    def imprimir(self):
        print(f"La ciudad es {self.lugar}")