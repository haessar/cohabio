import logging
from reportlab.pdfgen import canvas

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.contrib import messages
from .forms import ContactForm
from .functions.datetime_tools import request_counter
from .functions.geocoding_tools import GeoLocator
from .functions.google_API import max_entries
from .functions.main import compare_users
from .functions.prepare_markers import html_check

logger = logging.getLogger(__name__)

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

def search(request):
    if request.method == 'POST':
        quota_today = request_counter()
        logger.info('Total entries before: %i' % quota_today)
        if quota_today > max_entries:
            return render(request, 'mapper/splashscreen.html')
        search_id1 = request.POST.get('textfield1', None)
        search_id2 = request.POST.get('textfield2', None)
        transport_id1 = request.POST.getlist('transport1', None)
        transport_id2 = request.POST.getlist('transport2', None)
        max_commute_id1 = request.POST.get('maxcommute1', None)
        max_commute_id2 = request.POST.get('maxcommute2', None)
        request.session['sesh_work1'] = search_id1
        request.session['sesh_work2'] = search_id2
        request.session['sesh_tran1'] = html_check(transport_id1)[0]
        request.session['sesh_tran2'] = html_check(transport_id2)[0]
        request.session['sesh_mcom1'] = max_commute_id1
        request.session['sesh_mcom2'] = max_commute_id2
        request.session['sesh_chec1'] = html_check(transport_id1)[1]
        request.session['sesh_chec2'] = html_check(transport_id2)[1]
        error_message = ''
        if search_id1 == '' or search_id2 == '':
            error_message = 'Please tell us where you work!'
        elif transport_id1 == [] or transport_id2 == []:
            error_message = 'Please ensure transport options are selected!'
        elif search_id1 == search_id2:
            error_message = 'If you both work in the same place, why not live there!'
        if error_message:
            messages.add_message(request, messages.INFO, error_message)
            return HttpResponseRedirect('/')
        geolocator = GeoLocator(logger=logger)
        try:
            output = compare_users(
                locations=(search_id1, search_id2),
                modes=(transport_id1, transport_id2),
                times=(max_commute_id1, max_commute_id2),
                geolocator=geolocator
            )
            quota_today = request_counter()
            logger.info('Total entries after: {}'.format(quota_today))
        except Exception as e:
            logger.error(e)
            messages.add_message(request, messages.INFO, "We're not sure what happened...")
            return HttpResponseRedirect('/')
        else:
            if output == 'maxed':
                return render(request, 'mapper/splashscreen.html')
            if output == 'empty':
                messages.add_message(request, messages.INFO, 'No results! Try increasing commute times, or choosing a different transport method.')
                return HttpResponseRedirect('/')
            mean_gps = geolocator.average_gps(search_id1, search_id2)
            work_coords = geolocator.return_gps_from_place_names([search_id1, search_id2])
            work_names = [search_id1, search_id2]
            who = ["you", "they"]
            col = ["#428bca", "#d9534f"]
            work_places = list(zip([[wc.latitude, wc.longitude] for wc in work_coords], work_names, who, col))
            coords = [[float(place.latitude), float(place.longitude)] for place in output]
            html = [pl['html'] for pl in output.values()]
            context = {
                'mean_gps': mean_gps,
                'places': list(zip(coords, html)),
                'work_places': work_places,
            }
            request.session.update(context)
            request.session['user1modes'] = [modes.get('user1') for modes in output.values()]
            request.session['user2modes'] = [modes.get('user2') for modes in output.values()]
            request.session['locations'] = [str(loc) for loc in output.keys()]
            return render(request, 'mapper/map7.html', context)
    else:
        context = {
            'mean_gps': request.session['mean_gps'],
            'places': request.session['places'],
            'work_places': request.session['work_places'],
        }
        return render(request, 'mapper/map7.html', context)

def results_report(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="cohabio_report.pdf"'
    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response)
    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.setFont('Courier-Bold', 16)
    p.drawString(242, 800, "Cohabio Report")
    p.setFont('Courier-Bold', 9)
    p.drawString(30, 775, "Location")
    location1 = "Distance to " + str((request.session['sesh_work1'].split(","))[0])
    location2 = "Distance to " + str((request.session['sesh_work2'].split(","))[0])
    p.drawString(155, 775, location1)
    p.drawString(380, 775, location2)
    p.setFont('Courier', 9)
    position = 750
    locations = request.session['locations']
    user1modes = request.session['user1modes']
    user2modes = request.session['user2modes']

    def format_duration_line(user_modes):
        out_list = []
        for mode in user_modes:
            out_list.append(str(mode[0][0]) + ', ' + str(int(mode[0][1])) + ' mins')
        return out_list

    user1modetimes = format_duration_line(user1modes)
    user2modetimes = format_duration_line(user2modes)
    for idx, item in enumerate(locations):
        withcounter = str(idx + 1) + '. ' + item.strip()
        p.drawString(30, position, withcounter)
        position = position - 14
    position = 750
    for item in user1modetimes:
        p.drawString(155, position, item)
        position = position - 14
    position = 750
    for item in user2modetimes:
        p.drawString(380, position, item)
        position = position - 14
    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response

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
