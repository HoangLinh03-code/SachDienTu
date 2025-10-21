from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

converter = PdfConverter(
    artifact_dict=create_model_dict(),
)
rendered = converter(r"C:\Users\Admin\Desktop\Maru\SachDienTu\SDT\SDT_AMNHAC\SDT_AMNHAC_CTST_C1")
text, _, images = text_from_rendered(rendered)