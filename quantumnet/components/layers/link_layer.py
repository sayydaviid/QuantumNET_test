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
        self.logger = Logger.get_instance()
    
    @property
    def requests(self):
        return self._requests
    
    
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
        eprs = self._network.get_eprs_from_edge(channel)
        f1 = eprs[-1].get_current_fidelity()
        f2 = eprs[-2].get_current_fidelity()
        

        purification_prob = (f1 * f2) + ((1 - f1) * (1 - f2))
        if uniform(0, 1) < purification_prob:
            new_fidelity = (f1 * f2) / ((f1 * f2) + ((1 - f1) * (1 - f2)))
            epr_purificated = Epr(new_fidelity)
            self._network.physical_layer.add_epr_to_channel(epr_purificated, channel)
            return True
        # Se a purificação falhar
        return self._network.remove_epr(channel)

    def request(self, alice: Host, bob: Host):	
        """
        Solicita tentativa de criação de entrelaçamento.
        
        args:
            host_id : int : Id do host.
            target_host_id : int : Id do host alvo.
        """
        alice = self._network.get_host(alice)
        bob = self._network.get_host(bob)
        entangle = self._physical_layer.entanglement_creation_heralding_protocol(alice, bob)
        if entangle == True:
            self.logger.log(f'Entrelaçamento criado com sucesso entre Host {alice} e Host {bob}.')
        else:
            self.logger.log(f'O entrelaçamento não foi criado com sucesso.')	
 
    
    
    
        
        
    # def entanglement_generation_protocol(self, alice: int, bob: int, fidelity: float):
    #     """
    #     Protocolo de geração de entrelaçamento.
        
    #     args:
    #         alice : int : Id do host.
    #         bob : int : Id do host alvo.
    #         fidelity : float : Fidelidade mínima.
    #     """
    #     alice = self._network.get_host(alice)
    #     bob = self._network.get_host(bob)
    #     entangle = self._physical_layer.entanglement_creation_heralding_protocol(alice,bob)
    #     if entangle.fidelity < fidelity:
    #         self.logger.log(f'O Host {alice} solicitou tentativa de criação de entrelaçamento com o Host {bob}.')
    #         self.purification(alice,bob)
    #     else:
    #         self.logger.log(f'O Host {alice} solicitou tentativa de criação de entrelaçamento com o Host {bob}.')
    #         self.logger.log(f'Entrelaçamento criado com sucesso entre o Host {alice} e o Host {bob}.')
    #         self._requests.append(entangle)
    #    if entangle == True:
    #         self.logger.log(f'Entrelaçamento criado com sucesso entre Host {alice} e Host {bob}.')
    #     elif entangle == False:
    #         self._physical_layer.entanglement_creation_heralding_protocol(alice,bob)
    #         self.logger.log(f'Entrelaçamento criado com sucesso entre Host {alice} e Host {bob}.')
    #     else: 
    #         self.logger.log(f'Entrelaçamento não criado entre Host {alice} e Host {bob}.')
    #         self.purification(alice,bob)