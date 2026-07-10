import uproot

try:
    with uproot.open("/eos/user/d/dduan/FCCee/Hbs/mumu/initial_batch2/wzp6_ee_mumuH_Hcu_W4p1MeV_ecm240/chunk_5.root") as f:
        # Attempt to read the keys to ensure the file structure is intact
        f.keys()
    print("File is perfectly fine!")
except Exception as e:
    print(f"File is broken or corrupted: {e}")