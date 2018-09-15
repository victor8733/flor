#!/usr/bin/env python3


class ArtifactLight:

    def __init__(self, loc, name):
        self.loc = loc
        self.name = name

        self.resourceType = True
        self.parent = False
        self.max_depth = 0

    def set_produced(self):
        self.parent = True

    def get_location(self):
        # TODO: S3 case, API call
        return self.loc

    def get_isolated_location(self):
        location_array = self.loc.split('.')
        return "{}_{}.{}".format('.'.join(location_array[0:-1]), id(self), location_array[-1])

    def equals(self, other):
        return (type(self) == type(other)
                and self.loc == other.loc)
