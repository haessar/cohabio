from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMessage
from .forms import ContactForm


def index(request):
    context = {
        'loc1': str(request.session.get('sesh_work1', '')),
        'loc2': str(request.session.get('sesh_work2', '')),
        'tra1': request.session.get('sesh_tran1', ''),
        'tra2': request.session.get('sesh_tran2', ''),
        'tim1': str(request.session.get('sesh_mcom1', 45)),
        'tim2': str(request.session.get('sesh_mcom2', 45)),
        'che1': request.session.get('sesh_chec1', ['', '', '', '']),
        'che2': request.session.get('sesh_chec1', ['', '', '', '']),
    }
    return render(request, 'mapper/index_bootstrap.html', context)
    # return HttpResponse('Hello, welcome to the index page.')

def search(request):
    return HttpResponse('Hi, this is where an individual post will be.')

def acknowledgements (request):
    return render(request, 'mapper/acknowledgements.html')

def about (request):
    return render(request, 'mapper/about_us.html')

def contact(request):
    form_class = ContactForm
    if request.method == 'POST':
        if "submit" in request.POST:
            form = form_class(data=request.POST)
            if form.is_valid():
                contact_name = request.POST.get(
                    'contact_name'
                    , '')
                contact_email = request.POST.get(
                    'contact_email'
                    , '')
                form_content = request.POST.get('content', '')
                # Email the profile with the contact information
                template = get_template('mapper/contact_template.txt')
                context = Context({
                    'contact_name': contact_name,
                    'contact_email': contact_email,
                    'form_content': form_content,
                })
                content = template.render(context)
                email = EmailMessage(
                    "New contact form submission",
                    content,
                    "cohabio" + '',
                    ['contact.cohabio@gmail.com'],
                    headers={'Reply-To': contact_email}
                )
                email.send()
                next = request.GET.get('next', None)
                if next:
                    return HttpResponseRedirect(next)
        elif "back" in request.POST:
            next = request.GET.get('next', None)
            if next:
                return HttpResponseRedirect(next)
    return render(request, 'mapper/contact.html', {
        'form': form_class,
        'from': request.GET.get('from', None),
    })
