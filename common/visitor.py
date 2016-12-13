class BreakVisiting(Exception):
    pass

class ObjectVisitor():
    """
    The class defines common interface to traverse an object tree.

    A tree is defined by attribute with customizable name. The attribute
should be able to return an iterable of strings. Each string is name of
attribute which contains references to objects to traverse next.

    The iterable attribute name is '__visitable__' by default.  An example
of the iterable attribute type is list. The name of the attribute can be
customized by 'field_name' argument of base constructor.

    To traverse an object tree set 'root' __init__ attribute to the root
object and call 'visit'. 'on_visit' is not called for the root.

    Each time an object is visited the 'on_visit' method is called.
Reference to visited object is stored in self.cur. Reference and name
inside parent for current object is also stored in last entry of self.path

    Default 'on_visit' does nothing. The user should override it to define
needed behaviour.

    The 'on_visit' is called before traversing of subtree.

    To prevent traversing of subtree the on_visit can raise BreakVisiting.

    The 'replace' could be called to replace current object in its parent.
Note that 'replace' method internally raises BreakVisiting.

    Features (+) implemented, (-) TODO:
    - detection for cycles
    + visiting of simple reference to object
    + replacing of reference
    + visiting of references in list
    + replacement of reference in list
    + visiting of references in dictionary
    + replacement of references (values) in dictionary
    - visiting of references in tuple
    - replacement of reference in tuple (new tuple should be constructed
because the tuple class does not support editing)
    - recursive visiting of tuples, lists, dictionaries
    - replacement during recursive visiting of tuple
    - replacement during recursive visiting of list
    - replacement during recursive visiting of dictionary
    - 'on_leave' method which is called after traversing of subtree. Even if
traversing is skipped using BreakVisiting exception (including replacement).

    """
    def __init__(self, root, field_name = "__visitable__"):
        self.path = [(root,)]
        self.cur = root
        self.field_name = field_name

    def on_visit(self):
        # default method does nothing
        pass

    def replace(self, new_value):
        cur_container = self.path[-2][0]
        cur_name = self.path[-1][1]

        if    isinstance(cur_container, list) \
           or isinstance(cur_container, dict) \
        :
            cur_container[cur_name] = new_value
        elif isinstance(cur_container, object):
            setattr(cur_container, cur_name, new_value)
        else:
            raise Exception("Replacement for type %s is not implemented" %
                type(cur_container).__name__
            )

        self.path[-1] = (new_value, cur_name)
        self.cur = new_value

        # print self.path_str() + " <- " + str(new_value) 

        raise BreakVisiting()

    def path_str(self):
        return ".".join(str(n) + "{%s}" % str(o) for o, n in self.path[1:])

    def __push__(self, destination, path_name):
        self.path.append((destination, path_name))
        self.cur = destination

    def __pop__(self):
        self.path.pop()
        self.cur = self.path[-1][0]

    def __visit_fields__(self):
        try:
            visitable_list = getattr(self.cur, self.field_name)
        except AttributeError:
            pass
        else:
            for attribute_name in visitable_list:
                self.__visit__(attribute_name)

    visit = __visit_fields__

    def __visit_current__(self):
        try:
            self.on_visit()
        except BreakVisiting:
            return

        self.__visit_fields__()

    def __visit__(self, attribute_name):
        attr = getattr(self.cur, attribute_name)
        if isinstance(attr, list):
            self.__visit_list_attribute__(attr, attribute_name)
        elif isinstance(attr, dict):
            self.__visit_dictionary_attribute__(attr, attribute_name)
        elif isinstance(attr, object):
            self.__visit_object_attribute__(attr, attribute_name)

    def __visit_object_attribute__(self, attr, attribute_name):
        self.__push__(attr, attribute_name)
        self.__visit_current__()
        self.__pop__()

    def __visit_list_attribute__(self, attr, attribute_name):
        self.__push__(attr, attribute_name)
        for i, e in enumerate(attr):
            self.__push__(e, i)
            self.__visit_current__()
            self.__pop__()
        self.__pop__()

    def __visit_dictionary_attribute__(self, attr, attribute_name):
        self.__push__(attr, attribute_name)
        for k, e in attr.iteritems():
            self.__push__(e, k)
            self.__visit_current__()
            self.__pop__()
        self.__pop__()