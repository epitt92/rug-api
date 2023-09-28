import jinja2

def render_template(template, **kwargs):
    ''' renders a Jinja HTML template '''
    templateLoader = jinja2.FileSystemLoader(searchpath="email-templates/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templ = templateEnv.get_template(template)
    return templ.render(kwargs)

if __name__ == '__main__':
    print(render_template('referral-invite.html', data={'username': 'John', 'referrer': 'Jane', 'url': 'https://rug.ai'}))
