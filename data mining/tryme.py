
import pandas as pd
import shutil
from tabulate import tabulate
import matplotlib.pyplot as plt

def display_clean_table(df, columns_to_show, num_rows=10):
    """
    Display a clean, well-formatted table with borders in terminal
    Supports horizontal scrolling when table exceeds terminal width
    
    Args:
        df: Pandas DataFrame
        columns_to_show: List of columns to display
        num_rows: Number of rows to display
    """
    # Configure display options
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', 30)  # Reduced for better terminal display
    
    # Get terminal width
    try:
        terminal_width = shutil.get_terminal_size().columns
    except:
        terminal_width = 120
    
    # Prepare the table subset
    table_data = df[columns_to_show].head(num_rows)
    
    # Generate bordered table
    table_str = tabulate(
        table_data,
        headers='keys',
        tablefmt='grid',  # Use 'grid' for clean borders
        showindex=False,
        stralign='center',
        numalign='center'
    )
    
    # Calculate table width
    table_width = max(len(line) for line in table_str.split('\n')) if table_str else 0
    
    # Print header
    header_title = " PARLIAMENT QUESTIONS DATA "
    print("\n" + header_title.center(terminal_width, '='))
    print(f"Displaying first {num_rows} rows of {len(columns_to_show)} selected columns")
    print("=" * terminal_width)
    
    # Display the table with scrolling instructions if needed
    if table_width > terminal_width:
        print("\nNOTE: Table is wider than terminal. Use:")
        print("- Shift+Scroll (mouse)")
        print("- Shift+Arrow keys (← →)")
        print("- Touchpad horizontal scroll gestures\n")
    
    print(table_str)
    
    # Print footer with dataset info
    print("=" * terminal_width)
    print(f"• Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"• Selected Columns: {', '.join(columns_to_show)}")
    print(f"• Table Width: {table_width} chars | Terminal Width: {terminal_width} chars")
    print("=" * terminal_width + "\n")


# Example usage
if __name__ == "__main__":
    # Load the CSV
    df = pd.read_csv("/home/kahyata/data mining/datasets/parliament_questions.csv")

    # Select columns to display
    columns_to_show = [
        'document_title', 'date', 'year', 'question_number',
        'asked_by', 'minister', 'question_text'
    ]

    # Display the formatted table
    display_clean_table(df, columns_to_show, num_rows=10)

    # --- Diagnostics ---
    print("\nAvailable columns:", list(df.columns))
    print("\nSample data:\n", df.head())

    # --- Visualizations with matplotlib ---
    # 1. Number of questions per year
    if 'year' in df.columns and df['year'].notna().any():
        plt.figure(figsize=(8,4))
        df['year'].value_counts().sort_index().plot(kind='bar', color='skyblue')
        plt.title('Number of Parliament Questions per Year')
        plt.xlabel('Year')
        plt.ylabel('Number of Questions')
        plt.tight_layout()
        plt.show()
    else:
        print("[Warning] 'year' column missing or empty. Skipping year plot.")

    # 2. Top 10 MPs who asked the most questions
    if 'asked_by' in df.columns and df['asked_by'].notna().any():
        plt.figure(figsize=(8,4))
        df['asked_by'].value_counts().head(10).plot(kind='bar', color='orange')
        plt.title('Top 10 MPs by Number of Questions Asked')
        plt.xlabel('MP Name')
        plt.ylabel('Number of Questions')
        plt.tight_layout()
        plt.show()
    else:
        print("[Warning] 'asked_by' column missing or empty. Skipping MP plot.")

    # 3. Questions per Minister (Top 10)
    if 'minister' in df.columns and df['minister'].notna().any():
        plt.figure(figsize=(8,4))
        df['minister'].value_counts().head(10).plot(kind='bar', color='green')
        plt.title('Top 10 Ministers by Questions Received')
        plt.xlabel('Minister')
        plt.ylabel('Number of Questions')
        plt.tight_layout()
        plt.show()
    else:
        print("[Warning] 'minister' column missing or empty. Skipping minister plot.")