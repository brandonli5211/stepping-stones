import { createContext, useContext, useEffect, useState } from "react";

// Every in-app address, built in one place.
export const paths = {
  myCalls: "/",
  callDetail: (id = ":callId") => `/calls/${id}`,
  progress: "/progress",
  procedures: "/procedures",
};

/** matchPath("/calls/:callId", "/calls/7") → { callId: "7" }, or null. */
export function matchPath(pattern, path) {
  const want = pattern.split("/");
  const got = path.split("/");
  if (want.length !== got.length) return null;
  const params = {};
  for (let i = 0; i < want.length; i++) {
    if (want[i].startsWith(":")) params[want[i].slice(1)] = got[i];
    else if (want[i] !== got[i]) return null;
  }
  return params;
}

const RouterContext = createContext(null);
export const useRouter = () => useContext(RouterContext);

/** Picks the route for the current URL; unknown URLs show the first route. */
export function RouterProvider({ routes, children }) {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = (to) => {
    window.history.pushState(null, "", to);
    setPath(to);
  };

  let match = { route: routes[0], params: {} };
  for (const route of routes) {
    const params = matchPath(route.path, path);
    if (params) {
      match = { route, params };
      break;
    }
  }

  return <RouterContext.Provider value={{ navigate, match }}>{children}</RouterContext.Provider>;
}

export function RouteOutlet() {
  const { route, params } = useRouter().match;
  return <route.component params={params} />;
}

export function Link({ to, children, ...rest }) {
  const { navigate } = useRouter();
  const onClick = (e) => {
    e.preventDefault();
    navigate(to);
  };
  return (
    <a href={to} onClick={onClick} {...rest}>
      {children}
    </a>
  );
}
