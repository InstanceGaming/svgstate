import os
from dataclasses import dataclass
from typing import Iterable, List
from bs4 import BeautifulSoup, Tag
from argparse import ArgumentParser
from utils import fix_path


def namespaced(nss, name):
    assert nss, name
    return ':'.join((nss, name))


SOUP_BACKEND = 'lxml-xml'
INKSCAPE_NS = 'inkscape'
INKSCAPE_LABEL = namespaced(INKSCAPE_NS, 'label')
SVG_ROOT = 'svg'
SVG_GROUP = 'g'


def count_iterable(iterable):
    return sum([1 for _ in iterable])


@dataclass(frozen=True)
class State:
    
    @property
    def root(self):
        if not self.lineage:
            return None
        
        return self.lineage[-1]
    
    group: Tag
    lineage: List[Tag]
    parent_index: int
    parent_prefix: str


def get_cla():
    ap = ArgumentParser(description='Export SVG groups at a specific tree depth '
                                    'from a template SVG file to a new file with '
                                    'replicated canvas size and structure.')
    ap.add_argument('-d', '-depth',
                    required=True,
                    type=int,
                    dest='tree_depth')
    ap.add_argument('-p', '--pretty',
                    action='store_true',
                    dest='pretty')
    ap.add_argument('-e', '--encoding',
                    type=str,
                    default='utf-8',
                    dest='encoding')
    ap.add_argument(type=fix_path,
                    dest='input_file')
    ap.add_argument(type=fix_path,
                    dest='output_dir')
    return ap.parse_args()


def run():
    cla = get_cla()
    tree_depth = cla.tree_depth
    input_file = cla.input_file
    output_dir = cla.output_dir
    pretty = cla.pretty
    encoding = cla.encoding
    
    if tree_depth < 0:
        print('tree_depth must be positive')
        exit(2)
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(input_file, 'rb') as ipf:
            template_soup = BeautifulSoup(ipf,
                                          from_encoding=encoding,
                                          features=SOUP_BACKEND)
            states: List[State] = []
            
            # for each svg document in the file find all groups at the specified
            # depth in the tree structure and save metadata about each one
            svg_docs: Iterable[Tag] = template_soup.find_all(SVG_ROOT)
            doc_count = 0
            for svg_doc in svg_docs:
                group_tags: Iterable[Tag] = svg_doc.find_all(SVG_GROUP)

                # we want to keep a list of parents of this group, except for
                # parents of the svg tag, for reference later.
                # while we are at it, visit each parent of this group to
                # compile the prefix consisting of each parent's label
                # separated by dashes.
                for group_tag in group_tags:
                    node_depth = 0
                    parent_prefix = ''
                    lineage = []
                    
                    # iterates parents bottom-up
                    for parent in group_tag.parents:
                        # we do not care about the svg tag's parents
                        if parent in svg_doc.parents:
                            continue
                        
                        parent_label = parent.get(INKSCAPE_LABEL, '')
                        if parent_label:
                            parent_prefix += parent_label + '-'
                        
                        lineage.append(parent)
                        node_depth += 1
                        
                        # no sense in continuing if the depth already exceeds
                        # what we are looking for
                        if node_depth > tree_depth:
                            break

                    # filter out groups that are not at the desired tree depth
                    if node_depth == tree_depth:
                        # find the index of this tag within its parent
                        parent_index = -1
                        if lineage:
                            for parent_index, sibling in enumerate(lineage[0].children):
                                if sibling == group_tag:
                                    break
                            else:
                                parent_index = -1
                        
                        states.append(State(group_tag,
                                            lineage,
                                            parent_index,
                                            parent_prefix))
                
                doc_count += 1
            
            if not doc_count:
                print('no valid svg documents found in file')
                exit(4)
            
            for i, state in enumerate(states, start=1):
                # create a new svg document tag which has the same attributes
                # as the state group's original svg document to maintain the
                # canvas properties.
                state_soup = BeautifulSoup(features=SOUP_BACKEND)
                new_svg_doc = state_soup.new_tag(SVG_ROOT,
                                                 prefix=state.root.prefix,
                                                 namespace=state.root.namespace,
                                                 attrs=state.root.attrs)

                # then reconstruct the minimum internal structure to accommodate
                # our desired state group. we cannot just append the state group
                # by itself as parent groups are likely to have key
                # transformations applied, which effect all children objects.
                reversed_lineage = list(reversed(state.lineage))
                for j, relative in enumerate(reversed_lineage):
                    if relative == state.root:
                        continue
                    
                    previous_index = j - 1
                    if previous_index <= 0:
                        previous_node = new_svg_doc
                    else:
                        previous_node = reversed_lineage[previous_index]
                    
                    new_node = state_soup.new_tag(relative.name,
                                                  prefix=relative.prefix,
                                                  namespace=relative.namespace,
                                                  attrs=relative.attrs)
                    previous_node.append(new_node)
                
                # add our state group element at the end of the new tree.
                new_node.append(state.group)
                
                # add the svg root element to the document
                state_soup.append(new_svg_doc)
                
                state_label = state.group.get(INKSCAPE_LABEL)
                if state.parent_prefix and state_label:
                    name = state.parent_prefix + state_label
                elif state.parent_prefix and state.parent_index != -1 and not state_label:
                    # if we know the index of this tag within its parent
                    # then use it to identify this state unique to the parent
                    name = state.parent_prefix + str(state.parent_index + 1)
                else:
                    # otherwise, just use a sequence unique to the document
                    name = str(i)
                
                file_name = os.path.join(output_dir, f'{name}.{SVG_ROOT}')
                with open(file_name, 'wb') as opf:
                    if pretty:
                        markup = new_svg_doc.prettify(encoding=encoding)
                    else:
                        markup = new_svg_doc.encode(encoding=encoding)
                    opf.write(markup)
    except OSError as e:
        print(f'io error: {str(e)}')
        exit(3)

if __name__ == '__main__':
    run()
