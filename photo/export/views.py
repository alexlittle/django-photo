
import create_album

from django.http import HttpResponse, FileResponse

def make_view_pdf(request, album_id):
    album_url = create_album.make(album_id)
    response = FileResponse(open(album_url, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = "inline; filename=export-album"+ str(album_id) + ".pdf"
    return response

    