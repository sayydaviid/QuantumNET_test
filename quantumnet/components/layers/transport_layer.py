import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Logger, Epr
from random import uniform

class TransportLayer:
    def __init__(self, network, network_layer, link_layer, physical_layer):
        """
        Inicializa a camada de transporte.
        
        args:
            network : Network : Rede.
            network_layer : NetworkLayer : Camada de rede.
            link_layer : LinkLayer : Camada de enlace.
            physical_layer : PhysicalLayer : Camada física.
        """
        self._network = network
        self._network_layer = network_layer
        self._link_layer = link_layer
        self._physical_layer = physical_layer
        self.logger = Logger.get_instance()
        self.transmitted_qubits = []

    def __str__(self):
        """ Retorna a representação em string da camada de transporte. 
        
        returns:
            str : Representação em string da camada de transporte."""
        return f'Transport Layer'
    
    def request_transmission(self, alice_id: int, bob_id: int, num_qubits: int):
        """
        Requisição de transmissão de n qubits entre Alice e Bob.
        
        args:
            alice_id : int : Id do host Alice.
            bob_id : int : Id do host Bob.
            num_qubits : int : Número de qubits a serem transmitidos.
            
        returns:
            bool : True se a transmissão foi bem-sucedida, False caso contrário.
        """
        alice = self._network.get_host(alice_id)
        available_qubits = len(alice.memory)

        if available_qubits < num_qubits:
            self.logger.log(f'Número insuficiente de qubits na memória de Alice (Host:{alice_id}). Tentando transmitir os {available_qubits} qubits disponíveis.')
            num_qubits = available_qubits

        if num_qubits == 0:
            self.logger.log(f'Nenhum qubit disponível na memória de Alice ({alice_id}) para transmissão.')
            return False

        max_attempts = 2
        attempts = 0
        success = False

        while attempts < max_attempts and not success:
            # Estabelecer rota para cada qubit
            routes = []
            for _ in range(num_qubits):
                route = self._network_layer.short_route_valid(alice_id, bob_id)
                if route is None:
                    self.logger.log(f'Não foi possível encontrar uma rota válida na tentativa {attempts + 1}.')
                    break
                routes.append(route)
            
            if len(routes) == num_qubits:
                success = True
                for route in routes:
                    for i in range(len(route) - 1):
                        node1 = route[i]
                        node2 = route[i + 1]
                        # Verifica se há pelo menos um par EPR disponível no canal
                        if len(self._network.get_eprs_from_edge(node1, node2)) < 1:
                            self.logger.log(f'Falha ao encontrar par EPR entre {node1} e {node2} na tentativa {attempts + 1}.')
                            success = False
                            break
                    if not success:
                        break
            
            if not success:
                attempts += 1

        if success:
            # Registrar os qubits transmitidos
            for route in routes:
                qubit_info = {
                    'route': route,
                    'alice_id': alice_id,
                    'bob_id': bob_id,
                }
                self.transmitted_qubits.append(qubit_info)
            self.logger.log(f'Transmissão de {num_qubits} qubits entre {alice_id} e {bob_id} concluída com sucesso.')
            return True
        else:
            self.logger.log(f'Falha na transmissão de {num_qubits} qubits entre {alice_id} e {bob_id} após {attempts} tentativas.')
            return False
        
        
    def teleportation_protocol(self, alice_id: int, bob_id: int):
        """
        Realiza o protocolo de teletransporte de um qubit de Alice para Bob.
        
        args:
            alice_id : int : Id do host Alice.
            bob_id : int : Id do host Bob.
        
        returns:
            bool : True se o teletransporte foi bem-sucedido, False caso contrário.
        """
        # Estabelece uma rota válida
        route = self._network_layer.short_route_valid(alice_id, bob_id)
        if route is None:
            self.logger.log(f'Não foi possível encontrar uma rota válida para teletransporte entre {alice_id} e {bob_id}.')
            return False
        
        # Pega um qubit de Alice e um qubit de Bob
        alice = self._network.get_host(alice_id)
        bob = self._network.get_host(bob_id)
        
        if len(alice.memory) < 1 or len(bob.memory) < 1:
            self.logger.log(f'Alice ou Bob não possuem qubits suficientes para teletransporte.')
            return False
        
        qubit_alice = alice.memory.pop(0)  # Remove o primeiro qubit da memória de Alice
        qubit_bob = bob.memory.pop()       # Remove o último qubit da memória de Bob
        
        # Calcula a fidelidade final do teletransporte
        f_alice = qubit_alice.get_current_fidelity()
        f_bob = qubit_bob.get_current_fidelity()
        
        # Assume fidelidade do link como a média das fidelidades dos pares EPR na rota
        fidelities = []
        for i in range(len(route) - 1):
            epr_pairs = self._network.get_eprs_from_edge(route[i], route[i+1])
            fidelities.extend([epr.get_current_fidelity() for epr in epr_pairs])
        
        if not fidelities:
            self.logger.log(f'Não foi possível encontrar pares EPR na rota entre {alice_id} e {bob_id}.')
            return False
        
        f_route = sum(fidelities) / len(fidelities)
        
        # Fidelidade final do qubit teletransportado
        F_final = f_alice * f_bob * f_route + (1 - f_alice) * (1 - f_bob) * (1 - f_route)
        
        qubit_info = {
            'alice_id': alice_id,
            'bob_id': bob_id,
            'route': route,
            'fidelity_alice': f_alice,
            'fidelity_bob': f_bob,
            'fidelity_route': f_route,
            'F_final': F_final,
            'qubit_alice': qubit_alice,
            'qubit_bob': qubit_bob,
            'success': True
        }
        
        # Adiciona o qubit teletransportado à memória de Bob com a fidelidade final calculada
        qubit_alice.fidelity = F_final
        bob.memory.append(qubit_alice)
        self.logger.log(f'Teletransporte de qubit de {alice_id} para {bob_id} foi bem-sucedido com fidelidade final de {F_final}.')
        
        # Par virtual é deletado no final
        for i in range(len(route) - 1):
            self._network.remove_epr(route[i], route[i+1])
        
        self.transmitted_qubits.append(qubit_info)
        return True
    
    def run_transport_layer(self, alice_id: int, bob_id: int, num_qubits: int):
        """
        Executa a requisição de transmissão e o protocolo de teletransporte.
        
        args:
            alice_id : int : Id do host Alice.
            bob_id : int : Id do host Bob.
            num_qubits : int : Número de qubits a serem transmitidos.
            
        returns:
            bool : True se a operação foi bem-sucedida, False caso contrário.
        """
        alice = self._network.get_host(alice_id)
        bob = self._network.get_host(bob_id)
        available_qubits = len(alice.memory)

        if available_qubits < num_qubits:
            self.logger.log(f'Número insuficiente de qubits na memória de Alice (Host {alice_id}). Tentando transmitir os {available_qubits} qubits disponíveis.')
            num_qubits = available_qubits

        if num_qubits == 0:
            self.logger.log(f'Nenhum qubit disponível na memória de Alice ({alice_id}) para transmissão.')
            return False

        max_attempts = 2
        attempts = 0
        success = False
        routes = []

        while attempts < max_attempts and not success:
            routes.clear()
            for _ in range(num_qubits):
                route = self._network_layer.short_route_valid(alice_id, bob_id)
                if route is None:
                    self.logger.log(f'Não foi possível encontrar uma rota válida na tentativa {attempts + 1}.')
                    break
                routes.append(route)
            
            if len(routes) == num_qubits:
                success = True
                for route in routes:
                    for i in range(len(route) - 1):
                        node1 = route[i]
                        node2 = route[i + 1]
                        if len(self._network.get_eprs_from_edge(node1, node2)) < 1:
                            self.logger.log(f'Falha ao encontrar par EPR entre {node1} e {node2} na tentativa {attempts + 1}.')
                            success = False
                            break
                    if not success:
                        break
            
            if not success:
                attempts += 1

        if success:
            success_count = 0
            for route in routes:
                if len(alice.memory) < 1:
                    self.logger.log(f'Alice não possui qubits suficientes para teletransporte.')
                    continue

                qubit_alice = alice.memory.pop(0)

                # Criação da informação de teletransporte
                f_alice = qubit_alice.get_current_fidelity()

                fidelities = []
                for i in range(len(route) - 1):
                    epr_pairs = self._network.get_eprs_from_edge(route[i], route[i + 1])
                    fidelities.extend([epr.get_current_fidelity() for epr in epr_pairs])
                
                if not fidelities:
                    self.logger.log(f'Não foi possível encontrar pares EPR na rota entre {alice_id} e {bob_id}.')
                    continue
                
                f_route = sum(fidelities) / len(fidelities)

                # Pega um qubit de Bob
                if len(bob.memory) < 1:
                    self.logger.log(f'Bob não possui qubits suficientes para teletransporte.')
                    continue

                qubit_bob = bob.memory.pop(0)
                f_bob = qubit_bob.get_current_fidelity()

                # Fidelidade final do qubit teletransportado
                F_final = f_alice * f_bob * f_route + (1 - f_alice) * (1 - f_bob) * (1 - f_route)

                # Adiciona o qubit teletransportado à memória de Bob com a fidelidade final
                new_qubit = qubit_alice
                new_qubit.fidelity = F_final
                bob.memory.append(new_qubit)

                qubit_info = {
                    'alice_id': alice_id,
                    'bob_id': bob_id,
                    'route': route,
                    'fidelity_alice': f_alice,
                    'fidelity_bob': f_bob,
                    'fidelity_route': f_route,
                    'F_final': F_final,
                    'qubit_alice': qubit_alice,
                    'qubit_bob': qubit_bob,
                    'success': True
                }

                self.logger.log(f'Teletransporte de qubit de {alice_id} para {bob_id} foi bem-sucedido com fidelidade final de {F_final}.')

                # Remove os pares EPR usados na rota
                for i in range(len(route) - 1):
                    self._network.remove_epr(route[i], route[i + 1])

                self.transmitted_qubits.append(qubit_info)
                success_count += 1

            if success_count == num_qubits:
                self.logger.log(f'Transmissão e teletransporte de {num_qubits} qubits entre {alice_id} e {bob_id} concluídos com sucesso.')
                return True
            else:
                self.logger.log(f'Falha na transmissão de {num_qubits} qubits entre {alice_id} e {bob_id}.')
                return False
        else:
            self.logger.log(f'Falha na transmissão de {num_qubits} qubits entre {alice_id} e {bob_id} após {attempts} tentativas.')
            return False
    
    def get_transmitted_qubits(self):
        """
        Retorna a lista de qubits transmitidos.
        
        returns:
            list : Lista de dicionários contendo informações dos qubits transmitidos.
        """
        return self.transmitted_qubits

    def get_teleported_qubits(self):
        """
        Retorna a lista de qubits teletransportados.
        
        returns:
            list : Lista de dicionários contendo informações dos qubits teletransportados.
        """
        return self.transmitted_qubits



    # def run_transport_layer(self, alice_id: int, bob_id: int, num_qubits: int):
    #     """
    #     Executa a requisição de transmissão e o protocolo de teletransporte.
        
    #     args:
    #         alice_id : int : Id do host Alice.
    #         bob_id : int : Id do host Bob.
    #         num_qubits : int : Número de qubits a serem transmitidos.
            
    #     returns:
    #         bool : True se a operação foi bem-sucedida, False caso contrário.
    #     """
    #     alice = self._network.get_host(alice_id)
    #     bob = self._network.get_host(bob_id)
    #     available_qubits = len(alice.memory)

    #     if available_qubits < num_qubits:
    #         self.logger.log(f'Número insuficiente de qubits na memória de Alice (Host {alice_id}). Tentando transmitir os {available_qubits} qubits disponíveis.')
    #         num_qubits = available_qubits

    #     if num_qubits == 0:
    #         self.logger.log(f'Nenhum qubit disponível na memória de Alice ({alice_id}) para transmissão.')
    #         return False

    #     max_attempts = 2
    #     attempts = 0
    #     success = False
    #     routes = []

    #     while attempts < max_attempts and not success:
    #         routes.clear()
    #         for _ in range(num_qubits):
    #             route = self._network_layer.short_route_valid(alice_id, bob_id)
    #             if route is None:
    #                 self.logger.log(f'Não foi possível encontrar uma rota válida na tentativa {attempts + 1}.')
    #                 break
    #             routes.append(route)
            
    #         if len(routes) == num_qubits:
    #             success = True
    #             for route in routes:
    #                 for i in range(len(route) - 1):
    #                     node1 = route[i]
    #                     node2 = route[i + 1]
    #                     if len(self._network.get_eprs_from_edge(node1, node2)) < 1:
    #                         self.logger.log(f'Falha ao encontrar par EPR entre {node1} e {node2} na tentativa {attempts + 1}.')
    #                         success = False
    #                         break
    #                 if not success:
    #                     break
            
    #         if not success:
    #             attempts += 1

    #     if success:
    #         success_count = 0
    #         for route in routes:
    #             if len(alice.memory) < 1:
    #                 self.logger.log(f'Alice não possui qubits suficientes para teletransporte.')
    #                 continue

    #             qubit_alice = alice.memory.pop(0)

    #             # Criação da informação de teletransporte
    #             f_alice = qubit_alice.get_current_fidelity()

    #             fidelities = []
    #             for i in range(len(route) - 1):
    #                 epr_pairs = self._network.get_eprs_from_edge(route[i], route[i + 1])
    #                 fidelities.extend([epr.get_current_fidelity() for epr in epr_pairs])
                
    #             if not fidelities:
    #                 self.logger.log(f'Não foi possível encontrar pares EPR na rota entre {alice_id} e {bob_id}.')
    #                 continue
                
    #             f_route = sum(fidelities) / len(fidelities)

    #             # Pega um qubit de Bob
    #             if len(bob.memory) < 1:
    #                 self.logger.log(f'Bob não possui qubits suficientes para teletransporte.')
    #                 continue

    #             qubit_bob = bob.memory.pop(0)
    #             f_bob = qubit_bob.get_current_fidelity()

    #             # Fidelidade final do qubit teletransportado
    #             F_final = f_alice * f_bob * f_route + (1 - f_alice) * (1 - f_bob) * (1 - f_route)

    #             # Adiciona o qubit teletransportado à memória de Bob com a fidelidade final
    #             new_qubit = qubit_alice
    #             new_qubit.fidelity = F_final
    #             bob.memory.append(new_qubit)

    #             qubit_info = {
    #                 'alice_id': alice_id,
    #                 'bob_id': bob_id,
    #                 'route': route,
    #                 'fidelity_alice': f_alice,
    #                 'fidelity_bob': f_bob,
    #                 'fidelity_route': f_route,
    #                 'F_final': F_final,
    #                 'qubit_alice': qubit_alice,
    #                 'qubit_bob': qubit_bob,
    #                 'success': True
    #             }

    #             self.logger.log(f'Teletransporte de qubit de {alice_id} para {bob_id} foi bem-sucedido com fidelidade final de {F_final}.')

    #             # Remove os pares EPR usados na rota
    #             for i in range(len(route) - 1):
    #                 self._network.remove_epr(route[i], route[i + 1])

    #             self.transmitted_qubits.append(qubit_info)
    #             success_count += 1

    #         if success_count == num_qubits:
    #             self.logger.log(f'Transmissão e teletransporte de {num_qubits} qubits entre {alice_id} e {bob_id} concluídos com sucesso.')
    #             return True
    #         else:
    #             self.logger.log(f'Falha na transmissão de {num_qubits} qubits entre {alice_id} e {bob_id}.')
    #             return False
    #     else:
    #         self.logger.log(f'Falha na transmissão de {num_qubits} qubits entre {alice_id} e {bob_id} após {attempts} tentativas.')
    #         return False