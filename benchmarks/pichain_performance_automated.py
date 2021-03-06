"""This module is used to test the performance of the piChain package. It connects to a node instance and sends a
predefined number of transactions per seconds to see how many RPS (Requests per second) can be handled. The RPS rate is
increased automatically until piChain cannot handle it anymore.

Note: This script requires already running distributed_db processes (see module examples/distributed_db.py) where a
process listens on (localhost: 8000) for connections.
Note: set TESTING to False inside config.py to reach optimal performance.
"""

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.protocols.basic import LineReceiver


# Initial requests per second rate
RPS = 2000
# Step size in which RPS is increased
step_size = 1000
# number of seconds transactions are send at a specific RPS rate
running_time_per_RPS = 10
# Keeps track of how many transactions have been committed
txn_count = 0
# Keeps track of number of seconds the script is running
iterations = 0
# small commit delay is allowed in last round (given in seconds)
tolerance = 0.05
# try count per RPS
try_count_per_RPS = 5
current_try_count = 0


class Connection(LineReceiver):
    def lineReceived(self, line):
        global txn_count

        txn_count += 1

    def rawDataReceived(self, data):
        pass

    def connectionMade(self):
        self.send_txns()

    def timeout_over(self):
        """Verify that all transactions have been committed. If not stop, else initialize another round with increased
        RPS rate."""
        global iterations
        global RPS
        global txn_count

        iterations += 1
        if iterations % running_time_per_RPS == 0:
            # check if all txns have been committed, if not wait some tolerance time and try again
            if txn_count != RPS * running_time_per_RPS:
                deferLater(reactor, tolerance, self.verify_txns_committed)
            else:
                self.verify_txns_committed()
        else:
            self.send_txns()

    def verify_txns_committed(self):
        global txn_count
        global RPS

        # verify that all txns have been committed
        if txn_count == RPS * running_time_per_RPS:
            # update global variables and restart process
            if current_try_count % try_count_per_RPS == 0:
                RPS += step_size
            txn_count = 0
            self.send_txns()
        else:
            print(txn_count)
            print('performance test finished')
            print('piChain can handle %s RPS' % str(RPS - step_size))

    def send_txns(self):
        """Initiates the process of transactions beeing send."""
        self.send_batch(iterations)
        deferLater(reactor, 1, self.timeout_over)

    def send_batch(self, i):
        """Sends a predefined number (= RPS) of transactions as a batch to the node."""
        print('start iteration %s' % str(i))
        for j in range(0, RPS):
            self.send_msg(i, j)
        print('iteration %s is done' % str(i))

    def send_msg(self, i, j):
        msg = 'put k%i_%i v' % (i, j)
        self.sendLine(msg.encode())


class ClientFactory(ReconnectingClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        print('Resetting reconnection delay')
        self.resetDelay()
        return Connection()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


reactor.connectTCP('localhost', 8000, ClientFactory())
reactor.run()
