import re

default_ignore_file = '''# the blackjay directory
.blackjay/
# conflicted file copies
*.server_copy*
# vim temporary files
.*.swp
.*.swo
.*.swpx
.*.swx
# partially downloaded files
*.part
*.download
# lock files
*.lock
*.lck
# other temp file formats
*.temp
*.tmp
*~
'''

def load_ignore_patterns():
    ignf = open('.blackjay/ignore','r')
    igntext = ignf.read()
    ignf.close()

    patterns = []
    for pattern in igntext.split('\n'):
        if len(pattern) == 0 or pattern[0] == '#':
            continue
        # make periods literal
        pattern = re.sub('\.','\\\\.',pattern)
        # make "*" into ".*"
        pattern = re.sub('\*','.*',pattern)
        # add .* to the end of directory paths
        pattern = re.sub('/$','/.*',pattern)
        # append "$" to the end of non-empty patterns
        pattern = re.sub('(.)$','\\1$',pattern)
        # prepend / to the beginning of non-empty patterns
        pattern = re.sub('^(.)','/\\1',pattern)
        patterns.append(pattern)

    return patterns

def should_ignore(test,patterns):
    for p in patterns:
        if re.search(p,test) is not None:
            return True
    return False

