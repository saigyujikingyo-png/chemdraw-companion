// Developer probe adapter. Uses the locally installed vendor interop assembly;
// no vendor binaries are redistributed. Every Document argument is retained.
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;

public static class NativeChemDraw
{
    public sealed class SaveReceipt
    {
        public string RequestedPath;
        public string RequestedMime;
        public string[] ReturnedArguments;
        public string DocumentFullName;
        public bool Exists;
        public long Bytes;
        public long ElapsedMilliseconds;
    }

    public static SaveReceipt Save(object document, string requestedPath, string mime, double dpi)
    {
        // Never use a possibly changed ref argument as the requested destination.
        string destination = Path.GetFullPath(requestedPath);
        if (File.Exists(destination)) throw new IOException("Refusing to overwrite an artifact.");
        if (!Directory.Exists(Path.GetDirectoryName(destination)))
            throw new DirectoryNotFoundException("Artifact parent directory must already exist.");
        var native = (ChemDraw.IChemDrawDocument)document;
        object path = destination, format = mime, resolution = dpi;
        object width = Type.Missing, height = Type.Missing;
        var watch = Stopwatch.StartNew();
        // Let the actual vendor exception, including HRESULT, reach the journal.
        native.SaveAs(ref path, ref format, ref resolution, ref width, ref height);
        watch.Stop();
        return new SaveReceipt {
            RequestedPath = destination, RequestedMime = mime,
            ReturnedArguments = new [] { Describe(path), Describe(format), Describe(resolution), Describe(width), Describe(height) },
            DocumentFullName = native.FullName,
            Exists = File.Exists(destination),
            Bytes = File.Exists(destination) ? new FileInfo(destination).Length : 0,
            ElapsedMilliseconds = watch.ElapsedMilliseconds
        };
    }

    private static string Describe(object value)
    {
        if (value == null) return "null";
        if (value == Type.Missing) return "System.Reflection.Missing:<Missing>";
        return value.GetType().FullName + ":" + value.ToString();
    }

    public static object Open(object application, string path, string mime)
    {
        path=Path.GetFullPath(path);
        if(!File.Exists(path))throw new FileNotFoundException("Native input file does not exist.",path);
        object password = Type.Missing, format = mime;
        var document=((ChemDraw.IChemDrawApplication)application).Documents.Open(path, ref password, ref format);
        if(document==null)throw new InvalidOperationException("Native Open returned no document.");
        return document;
    }

    public static void Close(object document)
    {
        object save = false, path = Type.Missing;
        ((ChemDraw.IChemDrawDocument)document).Close(ref save, ref path);
    }

    public static void Position(object item, double x, double y)
    {
        // The vendor duplicates base properties in concrete interfaces; atoms
        // do not QueryInterface as IChemDrawObject on the tested build.
        var atom=item as ChemDraw.IChemDrawAtom;
        if(atom!=null) {var p=atom.Position;p.X=x;p.Y=y;atom.Position=p;return;}
        var text=item as ChemDraw.IChemDrawText;
        if(text!=null) {var p=text.Position;p.X=x;p.Y=y;text.Position=p;return;}
        var symbol=item as ChemDraw.IChemDrawSymbol;
        if(symbol!=null) {var p=symbol.Position;p.X=x;p.Y=y;symbol.Position=p;return;}
        throw new NotSupportedException("Position probe supports atom, text and symbol interfaces only.");
    }

    public static void SplinePoint(object item, int index, double x, double y)
    {
        var native=(ChemDraw.IChemDrawSpline)item;
        var point=native.GetPoint(index);
        if(point==null) throw new ArgumentOutOfRangeException("index", "Native spline point index is one based.");
        point.X=x; point.Y=y;
        native.SetPoint(index,point);
    }

    public static void Arrow(object item, double x1, double y1, double x2, double y2)
    {
        var native=(ChemDraw.IChemDrawArrow)item;
        var start=native.Start; start.X=x1; start.Y=y1; native.Start=start;
        var end=native.End; end.X=x2; end.Y=y2; native.End=end;
        native.ArrowHeadType=ChemDraw.CDArrowHeadType.kCDArrowHeadTypeSolid;
        native.ArrowHeadPositionStart=ChemDraw.CDArrowHeadPositionType.kCDArrowHeadPositionFull;
        native.ArrowHeadPositionTail=ChemDraw.CDArrowHeadPositionType.kCDArrowHeadPositionNone;
    }
    public static void LonePair(object item, double x1, double y1, double x2, double y2)
    {
        var native=(ChemDraw.IChemDrawSymbol)item;
        var start=native.Start; start.X=x1; start.Y=y1; native.Start=start;
        var end=native.End; end.X=x2; end.Y=y2; native.End=end;
    }
    public static void Caption(object item, string content, double size, double x, double y)
    {
        var native=(ChemDraw.IChemDrawText)item;
        native.Text=content;native.Family="Arial";native.Size=size;
        for(int i=1;i<=native.Styles.Count;i++) {
            var style=native.Styles.Item(i);style.Family="Arial";style.Size=size;
        }
        native.Settings.InterpretChemically=false;
        Position(item,x,y);
    }
    public static void Atom(object item, int element, double charge, int hydrogens)
    {
        var native=(ChemDraw.IChemDrawAtom)item;
        native.ElementNumber=element;native.Charge=charge;native.NumImplicitHydrogens=hydrogens;
    }
    public static object Data(object document, string mime)
    {
        var native=(ChemDraw.IChemDrawDocument)document;
        return native.Objects.get_Data(mime,Type.Missing,Type.Missing,Type.Missing);
    }
    public static bool SameIdentity(object left, object right)
    {
        if(left==null || right==null) return false;
        IntPtr a=IntPtr.Zero,b=IntPtr.Zero;
        try {a=Marshal.GetIUnknownForObject(left);b=Marshal.GetIUnknownForObject(right);return a==b;}
        finally {if(a!=IntPtr.Zero)Marshal.Release(a);if(b!=IntPtr.Zero)Marshal.Release(b);}
    }
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
    public static uint ApplicationProcess(object application)
    {
        var native=(ChemDraw.IChemDrawApplication)application;
        uint pid;GetWindowThreadProcessId(new IntPtr(native.MainWindow),out pid);return pid;
    }
    public static bool ActivateAndVerify(object application, object document)
    {
        var app=(ChemDraw.IChemDrawApplication)application;
        app.Visible=true;
        ((ChemDraw.IChemDrawDocument)document).Activate();
        return SameIdentity(app.ActiveDocument,document);
    }
    public static object FindAtom(object document, int id)
    {
        var d=(ChemDraw.IChemDrawDocument)document;
        for(int i=1;i<=d.Atoms.Count;i++){var n=d.Atoms.Item(i);if(n.ID==id)return n;}
        throw new ArgumentException("Native atom identity not found.");
    }
    public static object FindCurve(object document, int id)
    {
        var d=(ChemDraw.IChemDrawDocument)document;
        for(int i=1;i<=d.Splines.Count;i++){var n=d.Splines.Item(i);if(n.ID==id)return n;}
        throw new ArgumentException("Native curve identity not found.");
    }
    public static object FindSymbol(object document, int id)
    {
        var d=(ChemDraw.IChemDrawDocument)document;
        for(int i=1;i<=d.Symbols.Count;i++){var n=d.Symbols.Item(i);if(n.ID==id)return n;}
        throw new ArgumentException("Native symbol identity not found.");
    }
    public static double[] SymbolPoints(object symbol)
    {
        var s=(ChemDraw.IChemDrawSymbol)symbol;
        return new double[]{s.Start.X,s.Start.Y,s.End.X,s.End.Y};
    }
}
