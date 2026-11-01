import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from transcription import pack_matrix,configure
class TranscriptionTests(unittest.TestCase):
    def test_matrix_codec_preserves_every_module_and_row_boundary(self):
        for n in (21,25,29,33):
            rows=[[(x+3*y)%7==0 for x in range(n)] for y in range(n)]
            raw=bytes.fromhex(pack_matrix(rows,n));self.assertEqual(raw[0],n)
            for y in range(n):
                for x in range(n):
                    bit=y*n+x;self.assertEqual(bool(raw[1+bit//8]&(1<<(bit%8))),rows[y][x])
            self.assertEqual(len(raw),1+(n*n+7)//8)
    def test_invalid_template_or_non_boolean_data_rejected(self):
        rows=[[False]*21 for _ in range(21)]
        for expected in (25,True,20):
            with self.assertRaises(ValueError):pack_matrix(rows,expected)
        rows[0][0]=1
        with self.assertRaises(ValueError):pack_matrix(rows,21)
    def test_format_variants_do_not_invent_extra_information(self):
        for compact,encrypted in ((False,False),(False,True),(True,False),(True,True)):
            builder,cfg=configure('SeedTranscribeSeedQRFormatScreen',dict(is_compactqr=compact,is_encryptedqr=encrypted),{'top_nav':{},'button_list':['original']})
            if compact and encrypted:self.assertEqual(builder,'button_list_screen');self.assertNotIn('compact_text',cfg)
            else:
                self.assertEqual(cfg['show_compact'],compact or encrypted)
                self.assertEqual(cfg['compact_label'],'Encrypted' if encrypted else 'Compact')
            self.assertEqual(cfg['button_list'],['original'])

    def test_encrypted_reuses_matrix_and_original_titles_borders(self):
        from unittest.mock import patch
        for encrypted in (False,True):
            prefix='SeedTranscribeEncryptedQR' if encrypted else 'SeedTranscribeSeedQR'
            for suffix,builder in [('WholeQRScreen','seed_transcribe_whole_qr_screen'),('ZoomedInScreen','seed_transcribe_zoomed_qr_screen')]:
                with patch('transcription.matrix',return_value='public-matrix') as matrix:
                    actual,cfg=configure(prefix+suffix,dict(qr_data=b'public',num_modules=29),{'top_nav':{}})
                matrix.assert_called_once_with(b'public',29)
                self.assertEqual(actual,builder);self.assertEqual(cfg['matrix_hex'],'public-matrix')
                if suffix=='WholeQRScreen':
                    self.assertEqual(cfg['top_nav']['title'],'Transcribe Encrypted QR' if encrypted else 'Transcribe SeedQR')
                    self.assertEqual(cfg['button_list'],['Begin 29x29'])
                else:
                    self.assertEqual(cfg['border_modules'],5 if encrypted else 4)
                    self.assertFalse(cfg['allow_screensaver'])
