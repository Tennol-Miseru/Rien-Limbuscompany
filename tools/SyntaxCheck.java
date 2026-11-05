import com.sun.source.util.JavacTask;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/** Parse every Java 21 source without requiring remote Minecraft dependencies. */
public final class SyntaxCheck {
    public static void main(String[] args) throws Exception {
        Path root = Path.of(args.length > 0 ? args[0] : ".");
        List<Path> javaPaths = new ArrayList<>();
        try (var paths = Files.walk(root.resolve("src"))) {
            paths.filter(p -> p.toString().endsWith(".java")).forEach(javaPaths::add);
        }
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        DiagnosticCollector<JavaFileObject> sink = new DiagnosticCollector<>();
        try (StandardJavaFileManager manager = compiler.getStandardFileManager(sink, null, null)) {
            var units = manager.getJavaFileObjectsFromPaths(javaPaths);
            JavacTask task = (JavacTask) compiler.getTask(null, manager, sink,
                    List.of("-proc:none", "-source", "21"), null, units);
            task.parse();
        }
        long errors = sink.getDiagnostics().stream().filter(d -> d.getKind() == Diagnostic.Kind.ERROR).count();
        if (errors > 0) {
            sink.getDiagnostics().forEach(System.err::println);
            System.exit(1);
        }
        System.out.printf("PASS: %d Java 21 source files parse without syntax errors%n", javaPaths.size());
    }
}
