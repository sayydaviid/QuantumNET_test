import networkx as nx
from ...components import Host
from ..layers import *
from ...objects import Logger, Qubit, Epr

from random import uniform


# 1. EGP: Entanglement Generation Protocol
# -Camada de Enlace
# *Envia a Requisição de Tentativa de Criação de Entrelaçamento para camada física
# -Se sucesso, blz, se não tena dnv
# -Aqui sucesso, não é só a criação do entanglement, mas é ele com a fidalidade mínima
# -Pode optar por tentar criar novamente caso a fidelidade minima não esteja boa
# -Se deu ruim dnv, pode tentar purificar. (Estima, baseado na fidelidade min)
# *Pode enviar para vários links ao mesmo tempo


class LinkLayer():
    def __init__(self, network, physical_layer):
        """
        Inicializa a camada de enlace.
        
        args:
            network : Network : Rede.
            physical_layer : PhysicalLayer : Camada física.
        """
        self._network = network
        self._physical_layer = physical_layer
        self._requests = []
        self._failed_requests = []
        self.logger = Logger.get_instance()
    
    @property
    def requests(self):
        return self._requests
    
    @property
    def failed_requests(self):
        return self._failed_requests
    
    def __str__(self):
        """ Retorna a representação em string da camada de enlace. 
        
        returns:
            str : Representação em string da camada de enlace."""
        return f'Link Layer{self.link_layer_id}'


    def purification(self, channel: tuple):
        """
        Protocolo de purificação.
        """
        # TODO: Criar uma função tipo get_last_qubit() tira o último epr da lista de eprs!!!!
        # Não tá removendo o EPR do canal
        
        # Obtendo informações dos EPRs do canal
        alice, bob = channel
        eprs = self._network.get_eprs_from_edge(channel)
        f1 = eprs[-1].get_current_fidelity()
        f2 = eprs[-2].get_current_fidelity()
        

        purification_prob = (f1 * f2) + ((1 - f1) * (1 - f2))
        if uniform(0, 1) < purification_prob:
            new_fidelity = (f1 * f2) / ((f1 * f2) + ((1 - f1) * (1 - f2)))
            epr_purificated = Epr(new_fidelity)
            self._network.physical_layer.add_epr_to_channel(epr_purificated, (alice,bob))
            return True
        else:
        # Se a purificação falhar
            return self._network.remove_epr(channel)
        


    # def request(self, alice: Host, bob: Host):	
    #     """
    #     Solicita tentativa de criação de entrelaçamento.
        
    #     args:
    #         host_id : int : Id do host.
    #         target_host_id : int : Id do host alvo.
    #     """
    #     alice = self._network.get_host(alice)
    #     bob = self._network.get_host(bob)
    #     entangle = self._physical_layer.entanglement_creation_heralding_protocol(alice, bob)
    #     if entangle == True:
    #         self.logger.log(f'Entrelaçamento criado com sucesso entre Host {alice} e Host {bob}.')
    #     else:
    #         self.logger.log(f'O entrelaçamento não foi criado com sucesso.')	






    def request(self, alice: Host, bob: Host):    
        """
        Solicita tentativa de criação de entrelaçamento.
        
        args:
            host_id : int : Id do host.
            target_host_id : int : Id do host alvo.
        """
        alice = self._network.get_host(alice)
        bob = self._network.get_host(bob)
        for _ in range(2):  # Duas tentativas
            entangle = self._physical_layer.entanglement_creation_heralding_protocol(alice, bob)
            if entangle == True:
                self.logger.log(f'Entrelaçamento criado com sucesso entre Host {alice} e Host {bob}.')
                return  # Sai da função se o entrelaçamento for bem-sucedido
            else:
                # Se a tentativa falhar, adiciona o par EPR à lista de solicitações falhadas
                self._failed_requests.append((alice, bob))
        # Se as duas tentativas falharem, purifique os dois últimos pares EPR
        last_failed_requests = self._failed_requests[-2:]
        for request in last_failed_requests:
            if self.purification(request[0], request[1]):
                self.logger.log(f'A purificação do entrelaçamento entre Host {request[0]} e Host {request[1]} foi bem-sucedida.')
                self._failed_requests.remove(request)  # Remove o par EPR da lista de solicitações falhadas
            else:
                self.logger.log(f'A purificação do entrelaçamento falhou entre Host {request[0]} e Host {request[1]}.')
                self._network.remove_epr(request)
    
    
    
        
        
    