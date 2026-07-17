import ROOT
import os
from copy import deepcopy

ROOT.gROOT.SetBatch(True)

def clean_label(label):
    """Clean the label to remove parts after 'sel0_NoCuts'."""
    if 'sel0_NoCuts' in label:
        label = label.split('sel0_NoCuts')[0].rstrip('_')
    return label

def plot_root_histograms(root_files, input_dir, output_dir):
    """Plot histograms with the same name from different ROOT files on the same canvas."""
    # Check if output directory exists, if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    histograms = {}
    
    # List of known non-histogram objects to exclude
    non_histogram_objects = {"eventsProcessed", "sumOfWeights", "intLumi", "crossSection", "kfactor", "matchingEfficiency"}
    
    # Read histograms from all ROOT files
    for root_file in root_files:
        file_path = os.path.join(input_dir, root_file)
        print(f"Opening file: {file_path}")
        file = ROOT.TFile.Open(file_path)
        if not file or file.IsZombie():
            print(f"Error: Could not open file {file_path}")
            continue
        file_label = os.path.splitext(os.path.basename(root_file))[0].split('_', 2)[-1]  # Extract label for legend
        file_label = clean_label(file_label)
        
        for key in file.GetListOfKeys():
            obj_name = key.GetName()
            if obj_name in non_histogram_objects:
                continue  # Skip known non-histogram objects
            
            obj = key.ReadObj()
            if obj.InheritsFrom("TH1"):
                hist_name = obj.GetName()
                if hist_name not in histograms:
                    histograms[hist_name] = []
                histograms[hist_name].append((deepcopy(obj), file_label))
        
        file.Close()
    
    # Plot histograms with the same name on the same canvas
    for hist_name, hist_list in histograms.items():
        canvas_name = f"canvas_{hist_name}"
        canvas = ROOT.TCanvas(canvas_name, "Histogram Canvas", 800, 600)
        
        # Adjusting the legend and setting font size
        if hist_name in ["W_MC_m", "W_MC_p"]:
            legend = ROOT.TLegend(0.15, 0.7, 0.35, 0.88)  # Upper left position
        else:
            legend = ROOT.TLegend(0.7, 0.7, 0.88, 0.88)  # Default position
        legend.SetTextSize(0.03)  # Set the legend text size
        legend.SetBorderSize(0)  # Remove the border
        
        # Determine the maximum y-value to set the range
        max_y = max(hist.GetMaximum() for hist, _ in hist_list) * 1.2
        
        for idx, (hist, label) in enumerate(hist_list):
            if hist:
                hist.SetLineWidth(2)
                # Avoid the color green (index 3 in ROOT)
                color = idx + 1 if idx != 2 else idx + 2
                hist.SetLineColor(color)  # Use different colors
                if idx == 0:
                    hist.SetMaximum(max_y)  # Set the y-axis range to 20% more
                    hist.Draw("HIST")
                else:
                    hist.Draw("HIST SAME")
                legend.AddEntry(hist, label)
            else:
                print(f"Error: Histogram is None for {label}")
        
        legend.Draw()
        
        # Create file name
        output_file_name = f"{hist_name}"
        output_path = os.path.join(output_dir, output_file_name)
        
        # Save the plot
        canvas.SaveAs(f"{output_path}.pdf")
        canvas.SaveAs(f"{output_path}.png")
        canvas.Close()

if __name__ == "__main__":
    input_dir = "outputs_HInvjj/Validation_p6decay_Final"
    output_dir = "/eos/user/l/lia/www/FCC/HiggsInv/FullSim_Validation_test"
    root_files = [
        "output_ee_WW_enuenu_parent_sel0_NoCuts_histo.root",
        "output_ee_WW_munumunu_parent_sel0_NoCuts_histo.root",
        "output_ee_WW_lvqq_parent_sel0_NoCuts_histo.root"
    ]
    plot_root_histograms(root_files, input_dir, output_dir)