def pe_imports(p, expected):
    b = read(p, expected)
    image = ref(p, b)
    def u16(o):
        assert 0 <= o <= len(b)-2
        return struct.unpack_from('<H', b, o)[0]
    def u32(o):
        assert 0 <= o <= len(b)-4
        return struct.unpack_from('<I', b, o)[0]
    assert b[:2] == b'MZ'
    pe = u32(0x3c)
    assert b[pe:pe+4] == b'PE\x00\x00'
    coff = pe + 4
    count, opt_size = u16(coff+2), u16(coff+16)
    assert 0 < count <= 96
    opt = coff + 20
    magic = u16(opt)
    assert magic in (0x10b, 0x20b)
    numoff, diroff = (92, 96) if magic == 0x10b else (108, 112)
    assert opt_size >= diroff and opt+opt_size <= len(b)
    ndirs = u32(opt+numoff)
    assert ndirs <= (opt_size-diroff)//8
    headers = u32(opt+60)
    sections = []
    for n in range(count):
        o = opt+opt_size+n*40
        assert o+40 <= len(b)
        sections.append({'name': b[o:o+8].rstrip(b'\x00').decode('ascii'),
                         'virtual_size': u32(o+8), 'rva': u32(o+12),
                         'raw_size': u32(o+16), 'raw_offset': u32(o+20)})
    def offset(rva, size=1):
        if rva < headers and rva+size <= min(headers, len(b)):
            return rva
        matches = [s for s in sections if s['rva'] <= rva and
                   rva+size <= s['rva']+s['raw_size']]
        assert len(matches) == 1, ('unmapped/ambiguous RVA', rva, size)
        o = matches[0]['raw_offset'] + rva-matches[0]['rva']
        assert o+size <= len(b)
        return o
    def dllname(rva):
        o = offset(rva)
        chars = bytearray()
        for i in range(512):
            c = b[offset(rva+i)]
            if c == 0:
                name = chars.decode('ascii')
                assert name and '/' not in name and '\\' not in name
                return name, o
            chars.append(c)
        raise ValueError('unterminated DLL name')
    found, directories, unknown = [], [], []
    for index, label, width in [(1, 'IMPORT_DIRECTORY', 20), (13, 'DELAY_IMPORT_DIRECTORY', 32)]:
        if index >= ndirs:
            directories.append({'index': index, 'status': 'DIRECTORY_NOT_PRESENT'})
            continue
        d = opt+diroff+index*8
        rva, size = u32(d), u32(d+4)
        directories.append({'index': index, 'entry_file_offset': d, 'rva': rva, 'size': size})
        if rva == size == 0:
            continue
        assert rva and size >= width and size <= 1024*1024
        terminated = False
        for n in range(size//width):
            o = offset(rva+n*width, width)
            values = struct.unpack_from('<'+'I'*(width//4), b, o)
            if not any(values):
                terminated = True
                break
            if index == 13 and values[0] != 1:
                unknown.append({'basis': label, 'descriptor_file_offset': o,
                                'reason': 'DELAY_VA_OR_ATTRIBUTES_UNSUPPORTED', 'attributes': values[0]})
                continue
            name_rva = values[3] if index == 1 else values[1]
            name, no = dllname(name_rva)
            found.append({'dll_name': name, 'basis': 'STATIC_PE_'+label,
                          'image_ref': image, 'descriptor_file_offset': o,
                          'name_rva': name_rva, 'name_file_offset': no})
        assert terminated, ('missing null descriptor', str(p), label)
    return {'image_ref': image, 'pe_header_file_offset': pe, 'optional_magic': hex(magic),
            'sections': sections, 'directories': directories, 'imports': found, 'unknown': unknown}