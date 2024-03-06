def split_file(file_path, num_pieces):
    # Initialize an empty list to store pieces of data
    pieces_list = []

    # Open the file in binary mode
    with open(file_path, 'rb') as file:
        # Read the entire content of the file
        file_content = file.read()

        # Calculate the size of each piece
        piece_size = len(file_content) // num_pieces

        # Split the content into pieces
        for i in range(num_pieces):
            start_idx = i * piece_size
            end_idx = start_idx + piece_size
            # For the last piece, take the remaining content
            piece_data = file_content[start_idx:end_idx] if i != num_pieces - 1 else file_content[start_idx:]
            pieces_list.append(piece_data)

    return pieces_list


print(split_file(r"C:\Users\Owner\Downloads\ccsetup621.exe", 10000)[1])
