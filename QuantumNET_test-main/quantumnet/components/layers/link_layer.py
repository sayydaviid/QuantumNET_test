import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Logger, Epr
from random import uniform

class LinkLayer:
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
        return f'Link Layer'
    
    def request(self, alice_id: int, bob_id: int):
        """
        Solicita tentativa de criação de entrelaçamento.
        
        Args:
            alice_id : int : ID do host Alice.
            bob_id : int : ID do host Bob.
        """
        alice = self._network.get_host(alice_id)
        bob = self._network.get_host(bob_id)
        
        for _ in range(0):  # Duas tentativas
            entangle = self._physical_layer.entanglement_creation_heralding_protocol(alice, bob)
            if entangle:
                self.logger.log(f'Entrelaçamento criado com sucesso entre Host {alice_id} e Host {bob_id}.')
                return  # Sai da função se o entrelaçamento for bem-sucedido
            else:
                self._physical_layer.failed_eprs.append((entangle, alice_id, bob_id))
                self._failed_requests.append((alice_id, bob_id))        
                self.try_requests()
                self.logger.log(f'Tentativa para criação de par Epr')
            

  
    def try_requests(self):
        if len(self._physical_layer.failed_eprs) >= 2:
            last_failed_eprs = self._physical_layer.failed_eprs[-2:]
            for epr, alice_id, bob_id in last_failed_eprs:
                if self.purification(epr, alice_id, bob_id):
                    self.logger.log(f'A purificação do entrelaçamento foi bem-sucedida para o par EPR entre {alice_id} e {bob_id}.')
                    return False
                else:
                    self.logger.log(f'A purificação do entrelaçamento falhou para o par EPR entre {alice_id} e {bob_id}.')

                    

   
        
    # def request(self, alice_id: int, bob_id: int):    
    #     """
    #     Solicita tentativa de criação de entrelaçamento.
        
    #     Args:
    #         alice_id : int : ID do host Alice.
    #         bob_id : int : ID do host Bob.
    #     """
    #     alice = self._network.get_host(alice_id)
    #     bob = self._network.get_host(bob_id)
    #     for _ in range(2):  # Duas tentativas
    #         entangle = self._physical_layer.entanglement_creation_heralding_protocol(alice, bob)
    #         if entangle:
    #             self.logger.log(f'Entrelaçamento criado com sucesso entre Host {alice_id} e Host {bob_id}.')
    #             return  # Sai da função se o entrelaçamento for bem-sucedido
    #         else:
    #             # Se a tentativa falhar, adiciona o par EPR à lista de solicitações falhadas
    #             self._failed_requests.append((alice_id, bob_id))
    #     # Se as duas tentativas falharem, purifique os dois últimos pares EPR
    #     last_failed_requests = self._failed_requests[-2:]
    #     for request in last_failed_requests:
    #         if self.purification(*request):
    #             self.logger.log(f'A purificação do entrelaçamento entre Host {request[0]} e Host {request[1]} foi bem-sucedida.')
    #             self._failed_requests.remove(request)  # Remove o par EPR da lista de solicitações falhadas
    #         else:
    #             self.logger.log(f'A purificação do entrelaçamento falhou entre Host {request[0]} e Host {request[1]}.')
    #             self._network.remove_epr(*request)  # Corrigido aqui
                
    def purification(self, epr: Epr, alice_id: int, bob_id: int):
        """
        Protocolo de purificação.

        Args:
            alice_id (int): ID do host Alice.
            bob_id (int): ID do host Bob.
        """
        # Obtendo informações dos EPRs do canal
        failed_eprs = self._physical_layer.failed_eprs

        # Verificando se há pelo menos dois EPRs na lista de falhas
        if len(failed_eprs) < 2:
            self.logger.log(f'Não há EPRs suficientes para purificação no canal ({alice_id}, {bob_id}).')
            return False

        for failed_epr in failed_eprs:
            epr1, epr2 = failed_epr[0], failed_epr[1]
            
            # Verificar se epr1 e epr2 são instâncias de Epr
            if isinstance(epr1, Epr) and isinstance(epr2, Epr):
                f1 = epr1.get_current_fidelity()
                f2 = epr2.get_current_fidelity()
            else:
                # Lidar com o caso em que os elementos da lista não são instâncias de Epr
                self.logger.log('Os elementos na lista de EPRs falhados não são instâncias de Epr.')
                return False

            purification_prob = (f1 * f2) + ((1 - f1) * (1 - f2))
            if uniform(0, 1) < purification_prob:
                new_fidelity = (f1 * f2) / ((f1 * f2) + ((1 - f1) * (1 - f2)))
                epr_purified = Epr(new_fidelity)
                self._network.physical_layer.add_epr_to_channel(epr_purified, (alice_id, bob_id))
                self._physical_layer.failed_eprs.remove((epr1, alice_id, bob_id))
                self._physical_layer.failed_eprs.remove((epr2, alice_id, bob_id))
                return True
            else:
                # Se a purificação falhar
                self._physical_layer.failed_eprs.remove((epr1, alice_id, bob_id))
                self._physical_layer.failed_eprs.remove((epr2, alice_id, bob_id))
                return False


    
