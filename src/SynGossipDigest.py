class SynGossipDigest:

    def __init__(self, clusterId, gDigestList):
        self._clusterId = clusterId
        self._gDigestList = gDigestList

    def getGossipDigest(self):
        return self._gDigestList