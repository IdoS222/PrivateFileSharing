def download(owners, pieces, pieceSize, fileName, path, max_retries=3):
    def download_piece(piece_index):
        try:
            return True
        except Exception:
            return False

    pieces_per_owner = len(pieces) // len(owners)
    remaining_pieces = len(pieces) % len(owners)

    success_info = []

    def distribute_to_owner(owner, pieces_indices):
        for piece_index in pieces_indices:
            if download_piece(piece_index):
                success_info.append((owner, piece_index))

    for owner in owners:
        distribute_to_owner(owner, list(range(remaining_pieces)) + list(range(pieces_per_owner)))
        remaining_pieces -= 1

    retries = 0
    while retries < max_retries and any(piece_index < len(pieces) for _, piece_index in success_info):
        owner = owners[remaining_pieces % len(owners)]
        distribute_to_owner(owner, [piece_index for _, piece_index in success_info if piece_index < len(pieces)])
        remaining_pieces += 1
        retries += 1