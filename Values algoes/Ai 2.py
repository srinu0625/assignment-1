# Add the new sheet for summed P&L values and trade counts in the desired format
with pd.ExcelWriter(output_file_path, mode='a', engine='openpyxl') as writer:
    # First section: Algo summary
    summed_pl_df = pd.DataFrame({
        'Symbol': list(summed_pl.keys()),
        'Total P&L': list(summed_pl.values()),
        'Positive': [positive_trades[symbol] for symbol in symbols],
        'Negative': [negative_trades[symbol] for symbol in symbols],
    })

    # Add a row for the date
    summed_pl_df.loc[-1] = [f"Date: {previous_day.strftime('%Y-%m-%d')}", '', '', '']
    summed_pl_df.index = summed_pl_df.index + 1
    summed_pl_df = summed_pl_df.sort_index()

    # Append the algo summary to the Excel file
    summed_pl_df.to_excel(writer, index=False, sheet_name='Summary', startrow=1)

    # Total row for the first section
    total_row = pd.DataFrame({
        'Symbol': ['Total'],
        'Total P&L': [summed_pl_df['Total P&L'].sum()],
        'Positive': [summed_pl_df['Positive'].sum()],
        'Negative': [summed_pl_df['Negative'].sum()],
        'total':[summed_pl_df['Totalb P&L']]
    })
    total_row.to_excel(writer, index=False, sheet_name='Summary', startrow=len(summed_pl_df) + 2)
     
   
    # Second section: Existing positions
    existing_positions = pd.DataFrame({
        'Symbol': ['MNQZ4', 'MCLX4.CN', 'MGCZ4'],  # Example positions
        'Position': ['1 short', '3 short', '3 long'],  # Quantities and direction (long/short)
        'P&L': [87, 510, -147]  # Example P&L values
    })
    
    # Add an "Existing positions" title row
    title_df = pd.DataFrame({'Symbol': ['Existing positions'], 'Total P&L': ['P@I']})
    title_df.to_excel(writer, index=False, sheet_name='Summary', startrow=len(summed_pl_df) + 4)

    # Append the existing positions data
    existing_positions.to_excel(writer, index=False, sheet_name='Summary', startrow=len(summed_pl_df) + 6)

    # Total row for the second section
    total_positions_row = pd.DataFrame({
        'Symbol': ['Total'],
        'P&L': [existing_positions['P&L'].sum()]
    })
    total_positions_row.to_excel(writer, index=False, sheet_name='Summary', startrow=len(summed_pl_df) + 9)

print("Formatted data has been added to the final sheet.")
